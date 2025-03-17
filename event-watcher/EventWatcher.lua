local frame = CreateFrame("FRAME", "EventWatcherFrame")


frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_LOGOUT")
frame:RegisterEvent("GUILD_ROSTER_UPDATE")
frame:RegisterEvent("PLAYER_LEVEL_UP")


local versionMap = {
    [WOW_PROJECT_CLASSIC] = "classic",
    [WOW_PROJECT_BURNING_CRUSADE_CLASSIC] = "tbc-classic",
    [WOW_PROJECT_WRATH_CLASSIC] = "wrath-classic",
    [WOW_PROJECT_CATACLYSM_CLASSIC] = "cata-classic",
    [WOW_PROJECT_MAINLINE] = "retail"
}


local function InitializeStorage()
    -- EventWatcherDump = EventWatcherDump or {}
    -- EventWatcherDump.realms = EventWatcherDump.realms or {}
    -- EventWatcherDump.realms[GetRealmName()] = EventWatcherDump.realms[GetRealmName()] or {}
    EventWatcherDump = {}
    EventWatcherDump.realms = {}
    EventWatcherDump.realms[GetRealmName()] = {}

    EventWatcherDump["version"] = versionMap[WOW_PROJECT_ID]
    EventWatcherDump["region"] = GetCurrentRegionName():lower()
end

local function UpdateCurrentCharacter(newLevel)
    local realm = GetRealmName()
    local name = UnitName("player")
    local existingData = EventWatcherDump.realms[realm][name] or {}
    EventWatcherDump.realms[realm][name] = existingData
    EventWatcherDump.realms[realm][name].level = newLevel or UnitLevel("player") or existingData.level
    EventWatcherDump.realms[realm][name].class = UnitClass("player") or existingData.class
    EventWatcherDump.realms[realm][name].zone = GetZoneText() or GetRealZoneText() or existingData.zone
    EventWatcherDump.realms[realm][name].online = false
end

local function UpdateGuildRoster()
    local realm = GetRealmName()
    local numMembers = GetNumGuildMembers()
    for i = 1, numMembers do
        local name, _, _, level, class, zone, _, _, online = GetGuildRosterInfo(i)
        name = string.match(name, "([^-]+)")  -- Remove realm name if present
        local existingData = EventWatcherDump.realms[realm][name] or {}
        EventWatcherDump.realms[realm][name] = existingData
        EventWatcherDump.realms[realm][name].level = level or existingData.level
        EventWatcherDump.realms[realm][name].class = class or existingData.class
        EventWatcherDump.realms[realm][name].zone = zone or existingData.zone
        EventWatcherDump.realms[realm][name].online = (function() if online ~= nil then return online else return existingData.online end end)()
    end
end

local function SyncDeathlogData()
    local realm = GetRealmName()
    for name, watchData in pairs(EventWatcherDump.realms[realm]) do
        local uniqueID = deathlog_data_map and deathlog_data_map[realm] and deathlog_data_map[realm][name]
        if uniqueID then
            local deathData = deathlog_data and deathlog_data[realm] and deathlog_data[realm][uniqueID]
            if deathData then
                watchData.died_at = deathData.date
            else
            end
        else
        end
    end
end


frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        InitializeStorage()
        UpdateCurrentCharacter()
        GuildRoster()
        print("|cff00ff00EventWatcher:|r Initialized successfully")
    elseif event == "GUILD_ROSTER_UPDATE" then
        UpdateGuildRoster()
    elseif event == "PLAYER_LEVEL_UP" then
        local newLevel = ...
        UpdateCurrentCharacter(newLevel)
    elseif event == "PLAYER_LOGOUT" then
        SyncDeathlogData()
    end
end)
