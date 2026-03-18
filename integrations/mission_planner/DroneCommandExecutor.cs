using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using MissionPlanner.Comms;

namespace MissionPlanner
{
    /// <summary>
    /// Executes drone commands via Mission Planner's MAVLink connection
    /// </summary>
    public class DroneCommandExecutor
    {
        private MAVLinkInterface mavlink;

        /// <summary>
        /// Initialize the command executor with Mission Planner's MAVLink interface
        /// </summary>
        /// <param name="comPort">Mission Planner's MAVLink interface (MainV2.comPort)</param>
        public DroneCommandExecutor(MAVLinkInterface comPort)
        {
            mavlink = comPort;
        }

        /// <summary>
        /// Execute a drone command
        /// </summary>
        /// <param name="command">The command to execute</param>
        /// <returns>Result message</returns>
        public async Task<string> ExecuteCommand(DroneCommand command)
        {
            // Check if connected to drone
            if (mavlink == null || !mavlink.BaseStream.IsOpen)
            {
                return "[Error: Not connected to drone]";
            }

            if (command == null || string.IsNullOrEmpty(command.Type))
            {
                return "[Error: Invalid command]";
            }

            try
            {
                switch (command.Type.ToUpper())
                {
                    case "ARM":
                        return ArmDisarm(true);

                    case "DISARM":
                        return ArmDisarm(false);

                    case "TAKEOFF":
                        if (command.Parameters.ContainsKey("altitude"))
                        {
                            double altitude = Convert.ToDouble(command.Parameters["altitude"]);
                            return Takeoff(altitude);
                        }
                        return "[Error: TAKEOFF requires altitude parameter]";

                    case "LAND":
                        return Land();

                    case "RTL":
                        return ReturnToLaunch();

                    case "REBOOT":
                        return RebootFlightController();

                    case "CHANGE_MODE":
                        if (command.Parameters.ContainsKey("mode"))
                        {
                            string mode = command.Parameters["mode"].ToString();
                            return ChangeMode(mode);
                        }
                        return "[Error: CHANGE_MODE requires mode parameter]";

                    case "GOTO":
                        if (command.Parameters.ContainsKey("latitude") && command.Parameters.ContainsKey("longitude"))
                        {
                            double lat = Convert.ToDouble(command.Parameters["latitude"]);
                            double lon = Convert.ToDouble(command.Parameters["longitude"]);
                            double alt = command.Parameters.ContainsKey("altitude") ? Convert.ToDouble(command.Parameters["altitude"]) : 0;
                            return GoTo(lat, lon, alt);
                        }
                        return "[Error: GOTO requires latitude and longitude parameters]";

                    case "ALTITUDE_CHANGE":
                        if (command.Parameters.ContainsKey("altitude_change"))
                        {
                            double altitudeChange = Convert.ToDouble(command.Parameters["altitude_change"]);
                            return ChangeAltitude(altitudeChange);
                        }
                        return "[Error: ALTITUDE_CHANGE requires altitude_change parameter]";

                    case "GOTO_HOME":
                        return GoToHome();

                    case "MOVE_DIRECTION":
                        if (command.Parameters.ContainsKey("direction") && command.Parameters.ContainsKey("distance"))
                        {
                            string direction = command.Parameters["direction"].ToString();
                            double distance = Convert.ToDouble(command.Parameters["distance"]);
                            return MoveDirection(direction, distance);
                        }
                        return "[Error: MOVE_DIRECTION requires direction and distance parameters]";

                    case "GET_PARAM":
                        if (command.Parameters.ContainsKey("name"))
                        {
                            string paramName = command.Parameters["name"].ToString();
                            return GetParameter(paramName);
                        }
                        return "[Error: GET_PARAM requires name parameter]";

                    case "SET_PARAM":
                        if (command.Parameters.ContainsKey("name") && command.Parameters.ContainsKey("value"))
                        {
                            string paramName = command.Parameters["name"].ToString();
                            float paramValue = Convert.ToSingle(command.Parameters["value"]);
                            return SetParameter(paramName, paramValue);
                        }
                        return "[Error: SET_PARAM requires name and value parameters]";

                    case "LUA_SCRIPT":
                        return SaveLuaScript(command.Parameters);

                    default:
                        return $"[Error: Unknown command type: {command.Type}]";
                }
            }
            catch (Exception ex)
            {
                return $"[Error executing {command.Type}: {ex.Message}]";
            }
        }

        /// <summary>
        /// Arm or disarm the vehicle
        /// </summary>
        private string ArmDisarm(bool arm)
        {
            try
            {
                if (mavlink.doARM(mavlink.MAV.sysid, mavlink.MAV.compid, arm))
                {
                    return arm ? "✓ Armed" : "✓ Disarmed";
                }
                else
                {
                    return arm ? "[Error: Failed to arm]" : "[Error: Failed to disarm]";
                }
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Takeoff to specified altitude
        /// </summary>
        private string Takeoff(double altitude)
        {
            try
            {
                // Set mode to GUIDED first (required for takeoff)
                mavlink.setMode(mavlink.MAV.sysid, mavlink.MAV.compid, "GUIDED");
                
                // Small delay to ensure mode change
                System.Threading.Thread.Sleep(500);
                
                // Send takeoff command using the correct signature
                mavlink.doCommand(
                    (byte)mavlink.MAV.sysid,
                    (byte)mavlink.MAV.compid,
                    MAVLink.MAV_CMD.TAKEOFF,
                    0, 0, 0, 0,  // param1-4 (pitch, empty, empty, yaw)
                    0, 0,         // param5-6 (lat, lon - use current)
                    (float)altitude  // param7 (altitude)
                );

                return $"✓ Taking off to {altitude}m";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Land the vehicle
        /// </summary>
        private string Land()
        {
            try
            {
                // Set mode to LAND
                mavlink.setMode(mavlink.MAV.sysid, mavlink.MAV.compid, "LAND");
                return "✓ Landing";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Return to launch
        /// </summary>
        private string ReturnToLaunch()
        {
            try
            {
                // Set mode to RTL
                mavlink.setMode(mavlink.MAV.sysid, mavlink.MAV.compid, "RTL");
                return "✓ Returning to launch";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Reboot the flight controller
        /// </summary>
        private string RebootFlightController()
        {
            try
            {
                // Send reboot command to flight controller using MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN
                mavlink.doCommand(
                    mavlink.MAV.sysid,
                    mavlink.MAV.compid,
                    MAVLink.MAV_CMD.PREFLIGHT_REBOOT_SHUTDOWN,
                    1,  // Reboot autopilot
                    0, 0, 0, 0, 0, 0
                );
                return "✓ Rebooting flight controller";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Change flight mode
        /// </summary>
        private string ChangeMode(string mode)
        {
            try
            {
                // Set the requested mode
                mavlink.setMode(mavlink.MAV.sysid, mavlink.MAV.compid, mode.ToUpper());
                return $"✓ Mode changed to {mode.ToUpper()}";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Go to specified coordinates with optional altitude
        /// </summary>
        private string GoTo(double latitude, double longitude, double altitude = 0)
        {
            try
            {
                // Use setGuidedModeWP for more reliable GUIDED mode navigation
                // This is what Mission Planner uses internally for "Fly To Here"
                if (altitude == 0)
                {
                    altitude = mavlink.MAV.cs.alt; // Use current altitude if not specified
                }

                // Create Locationwp from coordinates
                var loc = new MissionPlanner.Utilities.Locationwp();
                loc.lat = latitude;
                loc.lng = longitude;
                loc.alt = (float)altitude;

                // Set guided mode waypoint
                mavlink.setGuidedModeWP(loc);

                if (altitude > 0)
                    return $"✓ Flying to {latitude}, {longitude} at {altitude}m";
                else
                    return $"✓ Flying to {latitude}, {longitude}";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Change altitude while maintaining current position
        /// </summary>
        private string ChangeAltitude(double altitudeChange)
        {
            try
            {
                // Get current position
                double currentLat = mavlink.MAV.cs.lat;
                double currentLon = mavlink.MAV.cs.lng;
                double currentAlt = mavlink.MAV.cs.alt;
                
                // Calculate new altitude
                double newAlt = currentAlt + altitudeChange;
                
                // Validate altitude
                if (newAlt < 0)
                {
                    return "[Error: Altitude cannot be negative]";
                }
                
                // Use GoTo with current position and new altitude
                var loc = new MissionPlanner.Utilities.Locationwp();
                loc.lat = currentLat;
                loc.lng = currentLon;
                loc.alt = (float)newAlt;
                
                mavlink.setGuidedModeWP(loc);
                
                string direction = altitudeChange > 0 ? "Ascending" : "Descending";
                return $"✓ {direction} {Math.Abs(altitudeChange)}m to {newAlt}m altitude";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Return to home position
        /// </summary>
        private string GoToHome()
        {
            try
            {
                // Get home position from MAVLink
                var home = mavlink.MAV.cs.HomeLocation;
                if (home == null)
                {
                    return "[Error: Home position not set]";
                }

                return GoTo(home.Lat, home.Lng, 0);
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Move in a specific direction by a certain distance
        /// </summary>
        private string MoveDirection(string direction, double distance)
        {
            try
            {
                // Ensure we're in GUIDED mode for movement
                mavlink.setMode(mavlink.MAV.sysid, mavlink.MAV.compid, "GUIDED");
                System.Threading.Thread.Sleep(500); // Wait for mode change
                
                // Get current position
                double currentLat = mavlink.MAV.cs.lat;
                double currentLon = mavlink.MAV.cs.lng;
                double currentAlt = mavlink.MAV.cs.alt;

                if (currentLat == 0 && currentLon == 0)
                {
                    return "[Error: Current position unknown]";
                }

                // Calculate bearing based on direction (4 cardinal directions only)
                double bearing = 0;
                switch (direction.ToUpper())
                {
                    case "NORTH": bearing = 0; break;
                    case "SOUTH": bearing = 180; break;
                    case "EAST": bearing = 90; break;
                    case "WEST": bearing = 270; break;
                    default:
                        return $"[Error: Unsupported direction '{direction}'. Use: north, south, east, or west]";
                }

                // Calculate new position using Haversine formula
                const double EARTH_RADIUS = 6371000; // meters
                double latRad = currentLat * Math.PI / 180.0;
                double lonRad = currentLon * Math.PI / 180.0;
                double bearingRad = bearing * Math.PI / 180.0;

                double newLatRad = Math.Asin(
                    Math.Sin(latRad) * Math.Cos(distance / EARTH_RADIUS) +
                    Math.Cos(latRad) * Math.Sin(distance / EARTH_RADIUS) * Math.Cos(bearingRad)
                );

                double newLonRad = lonRad + Math.Atan2(
                    Math.Sin(bearingRad) * Math.Sin(distance / EARTH_RADIUS) * Math.Cos(latRad),
                    Math.Cos(distance / EARTH_RADIUS) - Math.Sin(latRad) * Math.Sin(newLatRad)
                );

                double newLat = newLatRad * 180.0 / Math.PI;
                double newLon = newLonRad * 180.0 / Math.PI;

                // Use GOTO to move to new position
                return GoTo(newLat, newLon, currentAlt);
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Get a parameter value
        /// </summary>
        private string GetParameter(string paramName)
        {
            try
            {
                // Get parameter from MAVLink
                var param = mavlink.MAV.param[paramName];
                if (param == null)
                {
                    return $"[Error: Parameter {paramName} not found]";
                }

                return $"✓ {paramName} = {param.Value}";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Set a parameter value
        /// </summary>
        private string SetParameter(string paramName, float value)
        {
            try
            {
                // Set parameter via MAVLink
                mavlink.setParam(mavlink.MAV.sysid, mavlink.MAV.compid, paramName, value);
                return $"✓ Set {paramName} = {value}";
            }
            catch (Exception ex)
            {
                return $"[Error: {ex.Message}]";
            }
        }

        /// <summary>
        /// Save Lua script to Scripts/LuaScripts folder
        /// </summary>
        private string SaveLuaScript(Dictionary<string, object> parameters)
        {
            try
            {
                if (!parameters.ContainsKey("code"))
                {
                    return "✗ Error: No Lua code provided";
                }

                string luaCode = parameters["code"].ToString();
                string description = parameters.ContainsKey("description") ? parameters["description"].ToString() : "Custom script";
                string suggestedFilename = parameters.ContainsKey("suggested_filename") ? parameters["suggested_filename"].ToString() : "custom_script.lua";

                // Create Scripts/LuaScripts directory if it doesn't exist
                string scriptDir = System.IO.Path.Combine(
                    System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location),
                    "Scripts",
                    "LuaScripts"
                );
                System.IO.Directory.CreateDirectory(scriptDir);

                // Generate timestamped filename
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string baseFilename = System.IO.Path.GetFileNameWithoutExtension(suggestedFilename);
                string filename = $"{baseFilename}_{timestamp}.lua";
                string fullPath = System.IO.Path.Combine(scriptDir, filename);

                // Ensure the path is absolute
                fullPath = System.IO.Path.GetFullPath(fullPath);

                // Save the script
                System.IO.File.WriteAllText(fullPath, luaCode);

                // Verify file was created
                if (!System.IO.File.Exists(fullPath))
                {
                    return $"✗ Error: File was not created at {fullPath}";
                }

                var fileInfo = new System.IO.FileInfo(fullPath);

                return $"✓ Lua script saved: {filename}\n" +
                       $"📁 Location: {scriptDir}\n" +
                       $"💾 Full path: {fullPath}\n" +
                       $"📊 Size: {fileInfo.Length} bytes\n" +
                       $"📝 {description}";
            }
            catch (Exception ex)
            {
                return $"✗ Error saving Lua script: {ex.Message}";
            }
        }
    }
}

