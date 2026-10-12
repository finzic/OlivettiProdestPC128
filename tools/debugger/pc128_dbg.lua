-- pc128_dbg.lua - debug server for the PC128 (MAME pro128). Load with -autoboot_script.
-- Line protocol over a localhost TCP socket (MAME listens, the GUI connects):
--   request : "<id> <command> [args...]"
--   reply   : "<id> OK <key=value ...>"  or  "<id> ERR <message>"
--   event   : "0 EVT <name> <key=value ...>"
-- Environment: PC128_DBG_PORT (default 5555).

local PROTO = 1
local PORT = os.getenv("PC128_DBG_PORT") or "5555"

local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local space = cpu.spaces["program"]
local dbg = cpu.debug

local REGS = { "PC", "S", "U", "X", "Y", "A", "B", "DP", "CC" }

-- I/O window: a read has side effects (PIA flags, gate array), so it is refused unless forced.
local IO_LO, IO_HI = 0xA7C0, 0xA7FF

local conn = emu.file("", 7)
local rx = ""
local listening = false
local was_paused = false
local temp_bps = {}      -- breakpoint index -> true, removed on the next stop

local function reply(id, ok, body)
    conn:write(string.format("%s %s %s\n", id, ok and "OK" or "ERR", body or ""))
end

local function event(name, body)
    conn:write(string.format("0 EVT %s %s\n", name, body or ""))
end

-- Apply "bankN=entry,bankM=entry" overrides around fn(), then restore the CPU view.
local function with_banks(spec, fn)
    local saved = {}
    if spec and spec ~= "cpu" then
        for tag, entry in spec:gmatch("(%w+)=(%d+)") do
            local bank = machine.memory.banks[":" .. tag]
            if not bank then error("unknown bank " .. tag) end
            saved[bank] = bank.entry
            bank.entry = tonumber(entry)
        end
    end
    local ok, res = pcall(fn)
    for bank, old in pairs(saved) do bank.entry = old end
    if not ok then error(res, 0) end
    return res
end

local function hex(n) return string.format("%X", n) end
local function num(s) return tonumber(s, 16) end

local commands = {}

function commands.hello()
    return string.format("proto=%d machine=%s mame=%s", PROTO, emu.gamename(), emu.app_version())
end

function commands.state()
    return string.format("paused=%d", machine.paused and 1 or 0)
end

function commands.regs()
    local t = {}
    for _, r in ipairs(REGS) do
        t[#t + 1] = string.format("%s=%X", r, cpu.state[r].value)
    end
    return table.concat(t, " ")
end

function commands.setreg(args)
    local name, value = args[1] and args[1]:upper(), num(args[2] or "")
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
    local addr, len = num(args[1] or ""), num(args[2] or "")
    if not (addr and len) then error("usage: mem HEXADDR HEXLEN [bankN=entry,...|cpu] [force]") end
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

function commands.write(args)
    local addr, data = num(args[1] or ""), args[2]
    if not (addr and data and #data % 2 == 0) then error("usage: write HEXADDR HEXBYTES [spec]") end
    with_banks(args[3], function()
        for i = 1, #data, 2 do
            space:write_u8((addr + (i - 1) // 2) & 0xFFFF, tonumber(data:sub(i, i + 1), 16))
        end
    end)
    return "written=" .. (#data // 2)
end

function commands.bpset(args)
    local addr = num(args[1] or "")
    if not addr then error("usage: bpset HEXADDR [temp] [cond]") end
    local temp = args[2] == "temp"
    local cond = args[3] and table.concat(args, " ", 3)
    local idx = cond and dbg:bpset(addr, cond) or dbg:bpset(addr)
    if temp then temp_bps[idx] = true end
    return "index=" .. idx
end

function commands.bpclear(args)
    dbg:bpclear(tonumber(args[1]))
    return ""
end

function commands.bplist()
    local t = {}
    for idx, bp in pairs(dbg:bplist()) do
        t[#t + 1] = string.format("%d:%X:%s:%d", idx, bp.address, bp.condition ~= "" and bp.condition or "-",
            bp.enabled and 1 or 0)
    end
    table.sort(t)
    return table.concat(t, " ")
end

function commands.wpset(args)
    local addr, len = num(args[1] or ""), num(args[2] or "")
    local kind = args[3] or "rw"
    if not (addr and len) then error("usage: wpset HEXADDR HEXLEN r|w|rw [cond]") end
    local cond = args[4] and table.concat(args, " ", 4)
    local idx = cond and dbg:wpset(space, kind, addr, len, cond) or dbg:wpset(space, kind, addr, len)
    return "index=" .. idx
end

function commands.wpclear(args)
    dbg:wpclear(tonumber(args[1]))
    return ""
end

function commands.wplist()
    local t = {}
    for idx, wp in pairs(dbg:wplist(space)) do
        t[#t + 1] = string.format("%d:%X:%X:%s:%d", idx, wp.address, wp.length, wp.type,
            wp.enabled and 1 or 0)
    end
    table.sort(t)
    return table.concat(t, " ")
end

function commands.pause()
    emu.pause()
    return ""
end

function commands.go()
    dbg:go()
    emu.unpause()
    return ""
end

function commands.step(args)
    dbg:step(tonumber(args[1] or "1"))
    return ""
end

function commands.reset()
    machine:soft_reset()
    return ""
end

function commands.key(args)
    machine.natkeyboard:post(table.concat(args, " "))
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
    local args = { table.unpack(words, 3) }
    local ok, res = pcall(handler, args)
    reply(id, ok, ok and res or tostring(res))
end

local function poll()
    if not listening then
        listening = conn:open("socket.127.0.0.1:" .. PORT) == nil
        if not listening then return end
    end

    local chunk = conn:read(4096)
    if chunk and #chunk > 0 then
        rx = rx .. chunk
        while true do
            local nl = rx:find("\n", 1, true)
            if not nl then break end
            handle(rx:sub(1, nl - 1):gsub("\r", ""))
            rx = rx:sub(nl + 1)
        end
    end

    local paused = machine.paused
    if paused ~= was_paused then
        was_paused = paused
        if paused then
            for idx in pairs(temp_bps) do dbg:bpclear(idx) end
            temp_bps = {}
            event("paused", string.format("pc=%X", cpu.state["PC"].value))
        else
            event("running")
        end
    end
end

PC128_DBG_SUB = emu.register_periodic(poll)
emu.print_info("pc128_dbg: listening on 127.0.0.1:" .. PORT)
