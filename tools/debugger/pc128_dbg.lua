-- pc128_dbg.lua - debug server for the PC128 (MAME pro128), driven by tools/debugger/pc128dbg.py.
--
-- MAME must run with  -debug -debugger script -autoboot_script pc128_dbg.lua
-- ("script" is added by mame-patch/0003: the CPU stays stopped until this script resumes it).
--
-- Line protocol over a localhost TCP socket (MAME listens, one client connects):
--   request : "<id> <command> [args...]"
--   reply   : "<id> OK <payload>"   or   "<id> ERR <message>"
--   event   : "0 EVT <name> <payload>"
-- Free text (conditions, MAME console commands, typed text) travels hex-encoded.
--
-- Environment: PC128_DBG_PORT (default 5555), PC128_DBG_START ("run" default, or "stop").

local PROTO = 2
local PORT = os.getenv("PC128_DBG_PORT") or "5555"
local START = os.getenv("PC128_DBG_START") or "run"

local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local space = cpu.spaces["program"]
local dbg = cpu.debug
local debugger = machine.debugger
local nk = machine.natkeyboard

if not dbg or not debugger then
    emu.print_error("pc128_dbg: the MAME debugger is not enabled; start MAME with -debug -debugger script")
    return
end

local REGS = { "PC", "S", "U", "X", "Y", "A", "B", "DP", "CC" }
local IO_LO, IO_HI = 0xA7C0, 0xA7FF   -- reads have side effects (PIA flags): refused unless forced

local conn = emu.file("", 7)
local rx = ""
local listening = false
local last_state = nil
local last_paused = nil
local temp_bps = {}       -- breakpoint index -> true, removed on the next stop
local log_seen = 0        -- consolelog lines already reported
local frame = 0
local typing = nil        -- { lines = {...}, i = 1, gap = 0, line_gap = n }
local started = false

local function num(s) return s and tonumber(s, 16) end

local function unhex(s)
    if not s or s == "-" then return nil end
    return (s:gsub("..", function(h) return string.char(tonumber(h, 16)) end))
end

local function tohex(s)
    return (s:gsub(".", function(c) return string.format("%02X", c:byte()) end))
end

local function send(line)
    if listening then conn:write(line .. "\n") end
end

local function reply(id, ok, body)
    send(string.format("%s %s %s", id, ok and "OK" or "ERR", body or ""))
end

local function event(name, body)
    send(string.format("0 EVT %s %s", name, body or ""))
end

local function new_log_lines()
    local log = debugger.consolelog
    local out = {}
    for i = log_seen + 1, #log do out[#out + 1] = log[i] end
    log_seen = #log
    return out
end

-- Apply "bankN=entry,bankM=entry" overrides around fn(), then restore the CPU view.
local function with_banks(spec, fn)
    local saved = {}
    if spec and spec ~= "cpu" and spec ~= "-" then
        for tag, entry in spec:gmatch("(%w+)=(%d+)") do
            local bank = machine.memory.banks[":" .. tag]
            if not bank then error("unknown bank " .. tag) end
            saved[#saved + 1] = { bank, bank.entry }
            bank.entry = tonumber(entry)
        end
    end
    local ok, res = pcall(fn)
    for i = #saved, 1, -1 do saved[i][1].entry = saved[i][2] end
    if not ok then error(res, 0) end
    return res
end

local commands = {}

function commands.hello()
    return string.format("proto=%d machine=%s mame=%s", PROTO, (emu.gamename():gsub(" ", "_")), emu.app_version())
end

function commands.status()
    return string.format("state=%s paused=%d frame=%d pc=%X typing=%d throttle=%d",
        debugger.execution_state, machine.paused and 1 or 0, frame, cpu.state["PC"].value,
        typing and 1 or 0, machine.video.throttled and 1 or 0)
end

function commands.regs()
    local t = {}
    for _, r in ipairs(REGS) do
        t[#t + 1] = string.format("%s=%X", r, cpu.state[r].value)
    end
    return table.concat(t, " ")
end

function commands.setreg(args)
    local name, value = args[1] and args[1]:upper(), num(args[2])
    if name == "D" and value then
        cpu.state["A"].value = (value >> 8) & 0xFF
        cpu.state["B"].value = value & 0xFF
        return commands.regs()
    end
    if not (name and value and cpu.state[name]) then error("usage: setreg REG HEXVALUE") end
    cpu.state[name].value = value
    return commands.regs()
end

function commands.banks()
    local t = {}
    for tag, bank in pairs(machine.memory.banks) do
        t[#t + 1] = string.format("%s=%d", tag:sub(2), bank.entry)
    end
    table.sort(t)
    return table.concat(t, " ")
end

function commands.mem(args)
    local addr, len = num(args[1]), num(args[2])
    if not (addr and len) then error("usage: mem HEXADDR HEXLEN [banks|cpu|-] [force]") end
    local force = args[4] == "force"
    return with_banks(args[3], function()
        local out = {}
        for i = 0, len - 1 do
            local a = (addr + i) & 0xFFFF
            if not force and a >= IO_LO and a <= IO_HI then
                out[#out + 1] = "??"
            else
                out[#out + 1] = string.format("%02X", space:read_u8(a))
            end
        end
        return table.concat(out)
    end)
end

-- Banked RAM is written straight into the page behind the bank entry (needs the membank:write_u8
-- binding from mame-patch/0003): MAME's write handlers for $6000-$9FFF use the gate-array page, not
-- the bank entry, and a write to $B000-$EFFF would switch the cartridge bank instead of storing.
local BANKED = { { 0x6000, 0x7FFF, "bank7" }, { 0x8000, 0x9FFF, "bank8" },
                 { 0xB000, 0xBFFF, "bank10" }, { 0xC000, 0xEFFF, "bank11" } }

local function banked(a)
    for _, r in ipairs(BANKED) do
        if a >= r[1] and a <= r[2] then return machine.memory.banks[":" .. r[3]], a - r[1] end
    end
end

local function write_byte(a, v, override)
    local bank, off = banked(a)
    if bank and (override or a >= 0xB000) then
        if a >= 0xB000 and bank.entry < 8 then error(string.format("$%04X is ROM (read-only)", a), 0) end
        if not bank.write_u8 then error("MAME lacks membank:write_u8; rebuild it with tools/prepare-mame.sh", 0) end
        bank:write_u8(off, v)
    elseif (a >= 0xA000 and a < IO_LO) or a >= 0xF000 then
        error(string.format("$%04X is ROM (read-only)", a), 0)
    else
        space:write_u8(a, v)
    end
end

function commands.write(args)
    local addr, data = num(args[1]), args[2]
    if not (addr and data and #data % 2 == 0) then error("usage: write HEXADDR HEXBYTES [banks|cpu|-]") end
    local override = args[3] and args[3] ~= "-" and args[3] ~= "cpu"
    with_banks(args[3], function()
        for i = 1, #data, 2 do
            local a = (addr + (i - 1) // 2) & 0xFFFF
            local bank = banked(a)
            if (a >= 0xA000 and a < IO_LO) or a >= 0xF000 or (a >= 0xB000 and bank and bank.entry < 8) then
                error(string.format("$%04X is ROM (read-only)", a), 0)
            end
        end
        for i = 1, #data, 2 do
            write_byte((addr + (i - 1) // 2) & 0xFFFF, tonumber(data:sub(i, i + 1), 16), override)
        end
    end)
    return "written=" .. (#data // 2)
end

-- bpset ADDR FLAGS CONDHEX ACTIONHEX     FLAGS: "t" temporary, "-" normal
-- An invalid condition makes cpu.debug:bpset throw out of the Lua callback and wedges the server,
-- so parse it first with the CPU's symbols.
local expr_symbols = nil
local function check_expr(expr)
    if not expr then return end
    if not expr_symbols then
        -- the CPU's own debugger symbol table is not reachable from Lua: mirror the names it defines
        expr_symbols = emu.symbol_table(cpu)
        for name in pairs(cpu.state) do expr_symbols:add(name:lower(), 0) end
        for _, name in ipairs({ "curpc", "cycles", "totalcycles", "lastinstructioncycles", "wpaddr", "wpdata",
                                "wpsize", "beamx", "beamy", "frame", "cpunum", "logunmap" }) do
            expr_symbols:add(name, 0)
        end
        for name, n in pairs({ min = { 2, 2 }, max = { 2, 2 }, ["if"] = { 3, 3 }, abs = { 1, 1 }, bit = { 2, 3 },
                               s8 = { 1, 1 }, s16 = { 1, 1 }, s32 = { 1, 1 } }) do
            expr_symbols:add(name, n[1], n[2], function() return 0 end)
        end
    end
    local ok, err = pcall(function() return emu.parsed_expression(expr_symbols, expr) end)
    if not ok then error("bad condition '" .. expr .. "': " .. tostring(err), 0) end
end

function commands.bpset(args)
    local addr = num(args[1])
    if not addr then error("usage: bpset HEXADDR [t|-] [CONDHEX|-] [ACTIONHEX|-]") end
    local cond = unhex(args[3])
    check_expr(cond)
    local idx = dbg:bpset(addr, cond, unhex(args[4]))
    if args[2] == "t" then temp_bps[idx] = true end
    return "index=" .. idx
end

function commands.bpclear(args)
    if args[1] then dbg:bpclear(tonumber(args[1])) else dbg:bpclear() end
    return ""
end

function commands.bpenable(args)
    if args[2] == "0" then dbg:bpdisable(tonumber(args[1])) else dbg:bpenable(tonumber(args[1])) end
    return ""
end

function commands.bplist()
    local t = {}
    for idx, bp in pairs(dbg:bplist()) do
        t[#t + 1] = string.format("%d:%X:%d:%s", idx, bp.address, bp.enabled and 1 or 0,
            bp.condition ~= "" and tohex(bp.condition) or "-")
    end
    table.sort(t)
    return table.concat(t, " ")
end

-- wpset ADDR LEN r|w|rw CONDHEX ACTIONHEX
function commands.wpset(args)
    local addr, len = num(args[1]), num(args[2])
    if not (addr and len) then error("usage: wpset HEXADDR HEXLEN r|w|rw [CONDHEX|-] [ACTIONHEX|-]") end
    local cond = unhex(args[4])
    check_expr(cond)
    local idx = dbg:wpset(space, args[3] or "rw", addr, len, cond, unhex(args[5]))
    return "index=" .. idx
end

function commands.wpclear(args)
    if args[1] then dbg:wpclear(tonumber(args[1])) else dbg:wpclear() end
    return ""
end

function commands.wplist()
    local t = {}
    for idx, wp in pairs(dbg:wplist(space)) do
        t[#t + 1] = string.format("%d:%X:%X:%s:%d:%s", idx, wp.address, wp.length, wp.type,
            wp.enabled and 1 or 0, wp.condition ~= "" and tohex(wp.condition) or "-")
    end
    table.sort(t)
    return table.concat(t, " ")
end

function commands.stop()
    if machine.paused then emu.unpause() end
    debugger.execution_state = "stop"
    return ""
end

function commands.go(args)
    if machine.paused then emu.unpause() end
    local target = num(args[1])
    if target then dbg:go(target) else dbg:go() end
    return ""
end

function commands.step(args)
    dbg:step(tonumber(args[1] or "1"))
    return ""
end

-- MAME console command (hex-encoded); returns the new console output lines, hex-encoded, '|' separated.
function commands.mame(args)
    local cmd = unhex(args[1])
    if not cmd then error("usage: mame HEXCOMMAND") end
    new_log_lines()
    debugger:command(cmd)
    local out = {}
    for _, l in ipairs(new_log_lines()) do out[#out + 1] = tohex(l) end
    return table.concat(out, "|")
end

function commands.pause()
    emu.pause()
    return ""
end

function commands.unpause()
    emu.unpause()
    return ""
end

function commands.throttle(args)
    machine.video.throttled = args[1] ~= "0"
    return ""
end

function commands.reset(args)
    if args[1] == "hard" then machine:hard_reset() else machine:soft_reset() end
    return ""
end

-- type HEXTEXT [LINEGAPFRAMES]: '\r' separated lines are posted one at a time.
function commands.type(args)
    local text = unhex(args[1]) or ""
    local lines = {}
    for line in text:gmatch("([^\r]*)\r") do lines[#lines + 1] = line end
    local tail = text:match("([^\r]*)$")
    if tail and tail ~= "" then lines[#lines + 1] = tail end
    typing = { lines = lines, i = 1, gap = 0, line_gap = tonumber(args[2] or "6") }
    return "lines=" .. #lines
end

function commands.key(args)
    nk:post(unhex(args[1]) or "")
    return ""
end

function commands.snap()
    machine.video:snapshot()
    return ""
end

function commands.quit()
    machine:exit()
    return ""
end

local function handle(line)
    local words = {}
    for w in line:gmatch("%S+") do words[#words + 1] = w end
    local id, name = words[1], words[2]
    if not name then return end
    local handler = commands[name]
    if not handler then return reply(id, false, "unknown command " .. name) end
    local ok, res = pcall(handler, { table.unpack(words, 3) })
    reply(id, ok, ok and res or tostring(res))
end

local function nk_busy()
    local ok, v = pcall(function() return nk.is_posting end)
    if ok and v ~= nil then return v end
    ok, v = pcall(function() return not nk.empty end)
    return ok and v or false
end

local function on_frame()
    frame = frame + 1
    if typing then
        if typing.gap > 0 then
            typing.gap = typing.gap - 1
        elseif not nk_busy() then
            local line = typing.lines[typing.i]
            if line then
                nk:post(line .. "\r")
                typing.i = typing.i + 1
                typing.gap = typing.line_gap
            else
                typing = nil
                event("typed", "")
            end
        end
    end
end

local function poll()
    if not started then
        started = true
        if START ~= "stop" then dbg:go() end
    end
    if not listening then
        listening = conn:open("socket.127.0.0.1:" .. PORT) == nil
        if not listening then return end
    end

    local chunk = conn:read(65536)
    if chunk and #chunk > 0 then
        rx = rx .. chunk
        while true do
            local nl = rx:find("\n", 1, true)
            if not nl then break end
            handle((rx:sub(1, nl - 1):gsub("\r", "")))
            rx = rx:sub(nl + 1)
        end
    end

    local state = debugger.execution_state
    if state ~= last_state then
        last_state = state
        if state == "stop" then
            for idx in pairs(temp_bps) do dbg:bpclear(idx) end
            temp_bps = {}
            local reason = {}
            for _, l in ipairs(new_log_lines()) do
                if l:find("Stopped") or l:find("watchpoint") or l:find("breakpoint") then reason[#reason + 1] = l end
            end
            event("stopped", string.format("pc=%X reason=%s", cpu.state["PC"].value,
                #reason > 0 and tohex(table.concat(reason, "; ")) or "-"))
        else
            event("running", "")
        end
    end
    local paused = machine.paused
    if paused ~= last_paused then
        last_paused = paused
        event(paused and "paused" or "unpaused", "")
    end
end

PC128_DBG_SUB = emu.register_periodic(poll)
PC128_DBG_FRAME = emu.add_machine_frame_notifier(on_frame)
emu.print_info("pc128_dbg: listening on 127.0.0.1:" .. PORT)
