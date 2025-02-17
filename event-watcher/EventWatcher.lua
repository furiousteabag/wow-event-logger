local frame = CreateFrame("FRAME", "EventWatcherFrame")

frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_LEVEL_UP")
frame:RegisterEvent("PLAYER_LOGOUT")
frame:RegisterEvent("GUILD_ROSTER_UPDATE")

SLASH_EWADD1 = "/ewadd"
SLASH_EWREMOVE1 = "/ewremove"
SLASH_EWLIST1 = "/ewlist"

local function InitializeStorage()
    if not EventWatcherDump then
        EventWatcherDump = {}
    end
    if not EventWatcherDump.realms then
        EventWatcherDump.realms = {}
    end
    local currentRealm = GetRealmName()
    if not EventWatcherDump.realms[currentRealm] then
        EventWatcherDump.realms[currentRealm] = {
            watchlist = {}
        }
    end
    return currentRealm
end

local function UpdateCharactersData(characterNames)
    local currentRealm = GetRealmName()
    local numMembers = GetNumGuildMembers()
    local foundCharacters = {}
    -- Create a lookup table for faster character checking
    local watchedCharLookup = {}
    for _, name in ipairs(characterNames) do
        watchedCharLookup[name] = true
    end
    for i = 1, numMembers do
        local name, _, _, level, class, zone, _, _, online = GetGuildRosterInfo(i)
        name = string.match(name, "([^-]+)")  -- Remove realm name if present
        if watchedCharLookup[name] then
            EventWatcherDump.realms[currentRealm].watchlist[name] = {
                level = level,
                class = class,
                zone = zone,
                online = online
            }
            foundCharacters[name] = true
        end
    end
    return foundCharacters
end

local function UpdateWatchedCharactersData()
    local currentRealm = GetRealmName()
    if EventWatcherDump.realms[currentRealm] and EventWatcherDump.realms[currentRealm].watchlist then
        local characterNames = {}
        for characterName, _ in pairs(EventWatcherDump.realms[currentRealm].watchlist) do
            if characterName ~= UnitName("player") then
                table.insert(characterNames, characterName)
            end
        end
        if #characterNames > 0 then
            UpdateCharactersData(characterNames)
        end
    end
end

local function UpdateCurrentCharacter()
    local currentRealm = GetRealmName()
    local characterName = UnitName("player")
    EventWatcherDump.realms[currentRealm].watchlist[characterName] = {
        level = UnitLevel("player"),
        class = UnitClass("player"),
        zone = GetRealZoneText(),
        online = true
    }
end

SlashCmdList["EWADD"] = function(msg)
    if msg ~= "" then
        local currentRealm = GetRealmName()

        if EventWatcherDump.realms[currentRealm].watchlist[msg] then
            print("|cffff0000EventWatcher:|r Character " .. msg .. " is already in watchlist.")
            return
        end

        if UpdateCharactersData({msg}) then
            print("|cff00ff00EventWatcher:|r Added " .. msg .. " to watchlist.")
        else
            print("|cffff0000EventWatcher:|r Character " .. msg .. " not found in guild.")
        end
    else
        print("|cffff0000EventWatcher:|r Please provide a character name.")
    end
end

SlashCmdList["EWREMOVE"] = function(msg)
    if msg ~= "" then
        local currentRealm = GetRealmName()
        local characterName = UnitName("player")
        if msg == characterName then
            print("|cffff0000EventWatcher:|r Cannot remove yourself from watchlist.")
            return
        end
        if EventWatcherDump.realms[currentRealm].watchlist[msg] then
            EventWatcherDump.realms[currentRealm].watchlist[msg] = nil
            print("|cff00ff00EventWatcher:|r Removed " .. msg .. " from watchlist.")
        else
            print("|cffff0000EventWatcher:|r Character " .. msg .. " not found in watchlist.")
        end
    else
        print("|cffff0000EventWatcher:|r Please provide a character name.")
    end
end

SlashCmdList["EWLIST"] = function(msg)
    local currentRealm = GetRealmName()
    local watchlist = EventWatcherDump.realms[currentRealm].watchlist
    if not watchlist or next(watchlist) == nil then
        print("|cff00ff00EventWatcher:|r Watchlist is empty.")
        return
    end
    print("|cff00ff00EventWatcher:|r Current watchlist for realm " .. currentRealm .. ":")
    for name, data in pairs(watchlist) do
        if name ~= UnitName("player") then
            local status = data.online and "Online" or "Offline"
            print(string.format("%s: Level %d %s (%s) - %s",
                name, data.level, data.class, status, data.zone))
        end
    end
end

frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        local currentRealm = InitializeStorage()
        UpdateCurrentCharacter()
        GuildRoster()
        print("|cff00ff00EventWatcher:|r Initialized successfully for realm " .. currentRealm)

    elseif event == "PLAYER_LEVEL_UP" then
        local newLevel = ...
        UpdateCurrentCharacter()
        print("|cff00ff00EventWatcher:|r You reached level " .. newLevel)

    elseif event == "GUILD_ROSTER_UPDATE" then
        UpdateWatchedCharactersData()
    end
end)
