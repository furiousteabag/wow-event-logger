local frame = CreateFrame("FRAME", "EventWatcherFrame")

frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_LEVEL_UP")
frame:RegisterEvent("PLAYER_LOGOUT")
frame:RegisterEvent("GUILD_ROSTER_UPDATE")


SLASH_EWADD1 = "/ewadd"
SLASH_EWREMOVE1 = "/ewremove"
SLASH_EWLIST1 = "/ewlist"


local crossIcon = "\124TInterface\\TargetingFrame\\UI-RaidTargetingIcon_7:0\124t"
local triangleIcon = "\124TInterface\\TargetingFrame\\UI-RaidTargetingIcon_4:0\124t"


local function PreprocessName(name)
    return string.upper(string.sub(name, 1, 1)) .. string.lower(string.sub(name, 2))
end

local function GetFormattedPlayerLink(name)

    local data = EventWatcherDump.realms[GetRealmName()].watchlist[name]
    local level, class, zone, online = data.level, data.class, data.zone, data.online

    local status = online and triangleIcon or crossIcon

    local levelColor = GetQuestDifficultyColor(level)
    local levelColorCode = string.format("|cff%02x%02x%02x",
        levelColor.r * 255, levelColor.g * 255, levelColor.b * 255)
    local coloredLevel = levelColorCode .. level .. "|r"

    local classColor = RAID_CLASS_COLORS[string.upper(class)]
    local colorCode = classColor and string.format("|cff%02x%02x%02x",
        classColor.r * 255, classColor.g * 255, classColor.b * 255) or "|cffffffff"
    local coloredName = colorCode .. name .. "|r"

    local characterLink = GetPlayerLink(name, string.format("%s:%s", coloredLevel, coloredName))
    return string.format("%s[%s]", status, characterLink)
end

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
            table.insert(characterNames, characterName)
        end
        if #characterNames > 0 then
            UpdateCharactersData(characterNames)
        end
    end
end

local function UpdateCurrentCharacter(newLevel)
    local currentRealm = GetRealmName()
    local characterName = UnitName("player")
    EventWatcherDump.realms[currentRealm].watchlist[characterName] = {
        level = newLevel or UnitLevel("player"),
        class = UnitClass("player"),
        zone = GetZoneText() or GetRealZoneText(),
        online = true
    }
end


SlashCmdList["EWADD"] = function(name)
    if name ~= "" then
        name = PreprocessName(name)
        local currentRealm = GetRealmName()

        if EventWatcherDump.realms[currentRealm].watchlist[name] then
            print("|cffff0000EventWatcher:|r Character " .. GetFormattedPlayerLink(name) .. " is already in watchlist.")
            return
        end

        if UpdateCharactersData({name})[name] then
            print("|cff00ff00EventWatcher:|r Added " .. GetFormattedPlayerLink(name) .. " to watchlist.")
        else
            print("|cffff0000EventWatcher:|r Character " .. name .. " not found in guild.")
        end
    else
        print("|cffff0000EventWatcher:|r Please provide a character name.")
    end
end

SlashCmdList["EWREMOVE"] = function(name)
    if name ~= "" then
        name = PreprocessName(name)
        local currentRealm = GetRealmName()
        if EventWatcherDump.realms[currentRealm].watchlist[name] then
            local formattedPlayerLink = GetFormattedPlayerLink(name)
            EventWatcherDump.realms[currentRealm].watchlist[name] = nil
            print("|cff00ff00EventWatcher:|r Removed " .. formattedPlayerLink .. " from watchlist.")
        else
            print("|cffff0000EventWatcher:|r Character " .. name .. " not found in watchlist.")
        end
    else
        print("|cffff0000EventWatcher:|r Please provide a character name.")
    end
end

SlashCmdList["EWLIST"] = function()
    local currentRealm = GetRealmName()
    local watchlist = EventWatcherDump.realms[currentRealm].watchlist
    if not watchlist or next(watchlist) == nil then
        print("|cff00ff00EventWatcher:|r Watchlist is empty.")
        return
    end
    print("|cff00ff00EventWatcher:|r Current watchlist for realm " .. currentRealm .. ":")
    for name, data in pairs(watchlist) do
        local formattedPlayerLink = GetFormattedPlayerLink(name)
        print(string.format("%s %s", formattedPlayerLink, data.zone))
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
        UpdateCurrentCharacter(newLevel)
        print("|cff00ff00EventWatcher:|r You reached level " .. newLevel)
    elseif event == "GUILD_ROSTER_UPDATE" then
        UpdateWatchedCharactersData()
    end
end)
