-- harness.lua  -  MAME autoboot script for the PC128 / Thomson MO6 harness.
-- pc128.py prepends a `CONFIG = {...}` table to this file and passes the result
-- to MAME with -autoboot_script. Do not run it by hand.
--
-- CONFIG fields:
--   mode           "basic" | "asm"
--   boot_frames    frames to wait for the machine to reach the boot menu
--   menu_key       key typed at the boot menu ("1" = BASIC 128, "2" = BASIC 1.0)
--   menu_frames    frames to wait after menu_key for the BASIC prompt
--   line_gap_frames  pause between typed BASIC lines
--   run_frames     max frames to let the program run before stopping
--   done_addr      optional RAM address; program stores non-zero there to finish early
--   done_page      RAM page (0-7) holding done_addr at $6000-$9FFF, nil = CPU view
--   dumps          { {addr=, len=, page=, label=}, ... } memory ranges to report
--   data_banks     MAME bank tags behind $6000-$7FFF and $8000-$9FFF
--   basic_lines    (basic) lines to type, already including NEW / RUN
--   segments       (asm) { {addr=..., hex="..."}, ... }
--   entry          (asm) address to jump to
--   result_path    file the results are written to

local CFG = CONFIG

-- ---------------------------------------------------------------- compat ----
local function get_machine()
    if type(manager.machine) == "function" then
        return manager:machine()          -- old MAME API
    end
    return manager.machine                -- MAME 0.227+
end

local machine = get_machine()
local cpu     = machine.devices[":maincpu"]
local mem     = cpu.spaces["program"]
local nk      = machine.natkeyboard

-- ----------------------------------------------------------------- state ----
local frame      = 0
local phase      = "boot"
local queue_i    = 1
local gap        = 0
local run_start  = 0
local finish_at  = nil
local status     = "timeout"
local notes      = {}

local function note(s) notes[#notes + 1] = s end

-- Access RAM page `page` (0-7) at $6000-$9FFF by switching the MAME bank around the access.
local function with_page(addr, page, fn)
    if not page then return fn() end
    local tag = CFG.data_banks[addr < 0x8000 and 1 or 2]
    local bank = machine.memory.banks[tag]
    if not bank then
        note("bank " .. tostring(tag) .. " not found; reading CPU view")
        return fn()
    end
    local old = bank.entry
    bank.entry = page
    local ok, v = pcall(fn)
    bank.entry = old
    if not ok then error(v) end
    return v
end

local function read_u8(addr, page)
    return with_page(addr, page, function() return mem:read_u8(addr) end)
end

local function write_u8(addr, value, page)
    with_page(addr, page, function() mem:write_u8(addr, value) end)
end

local function nk_busy()
    local ok, v = pcall(function() return nk.is_posting end)
    if ok and v ~= nil then return v end
    ok, v = pcall(function() return not nk.empty end)
    if ok and v ~= nil then return v end
    return false
end

local function load_segments()
    for _, seg in ipairs(CFG.segments or {}) do
        local h = seg.hex
        for i = 1, #h, 2 do
            mem:write_u8(seg.addr + (i - 1) // 2, tonumber(h:sub(i, i + 1), 16))
        end
    end
end

local function set_reg(name, value)
    local ok, err = pcall(function() cpu.state[name].value = value end)
    if not ok then note("could not set " .. name .. ": " .. tostring(err)) end
end

-- ---------------------------------------------------------------- result ----
local REGS = { "PC", "S", "U", "X", "Y", "A", "B", "DP", "CC" }

local function write_result()
    local f = io.open(CFG.result_path, "w")
    if not f then return end
    f:write("status ", status, "\n")
    f:write("frames ", tostring(frame), "\n")
    for _, name in ipairs(REGS) do
        local ok, v = pcall(function() return cpu.state[name].value end)
        if ok and v then f:write(string.format("reg %s=%X\n", name, v)) end
    end
    for _, d in ipairs(CFG.dumps or {}) do
        local bytes = {}
        for i = 0, d.len - 1 do
            local ok, v = pcall(read_u8, d.addr + i, d.page)
            bytes[#bytes + 1] = string.format("%02X", ok and v or 0)
        end
        f:write(string.format("mem %s %s\n", d.label, table.concat(bytes)))
    end
    for _, n in ipairs(notes) do f:write("note ", n, "\n") end
    f:close()
end

local function begin_finish()
    pcall(function() machine.video:snapshot() end)   -- PNG lands in -snapshot_directory
    finish_at = frame + 3                             -- let the snapshot happen
end

-- ------------------------------------------------------------ frame loop ----
local function on_frame()
    frame = frame + 1

    if finish_at then
        if frame >= finish_at then
            write_result()
            machine:exit()
        end
        return
    end

    if phase == "boot" then
        if frame >= CFG.boot_frames then
            -- PC128 boots into a menu: 1 = BASIC 128, 2 = BASIC 1.0
            if CFG.menu_key and CFG.menu_key ~= "" then
                nk:post(CFG.menu_key)
                phase, gap = "menu", CFG.menu_frames
            else
                phase = "ready"
            end
        end

    elseif phase == "menu" then
        if gap > 0 then gap = gap - 1 else phase = "ready" end

    elseif phase == "ready" then
        if CFG.done_addr then write_u8(CFG.done_addr, 0, CFG.done_page) end
        if CFG.mode == "asm" then
            load_segments()
            set_reg("PC", CFG.entry)
            phase, run_start = "run", frame
        else
            phase = "type"
        end

    elseif phase == "type" then
        if gap > 0 then gap = gap - 1; return end
        if nk_busy() then return end
        local line = CFG.basic_lines[queue_i]
        if line then
            nk:post(line .. "\r")
            queue_i = queue_i + 1
            gap = CFG.line_gap_frames
        else
            phase, run_start = "run", frame
        end

    elseif phase == "run" then
        if CFG.done_addr and read_u8(CFG.done_addr, CFG.done_page) ~= 0 then
            status = "done"
            begin_finish()
        elseif frame - run_start >= CFG.run_frames then
            begin_finish()
        end
    end
end

-- Keep a global reference: MAME unsubscribes the notifier if it is garbage collected.
if emu.add_machine_frame_notifier then
    FRAME_SUB = emu.add_machine_frame_notifier(on_frame)
else
    emu.register_frame_done(on_frame)
end
