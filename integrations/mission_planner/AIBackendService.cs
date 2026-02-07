using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace MissionPlanner
{
    /// <summary>
    /// Service class to communicate with the ArduPilot AI Backend HTTP API
    /// </summary>
    public class AIBackendService
    {
        private readonly HttpClient httpClient;
        private readonly string backendUrl;
        private readonly int timeoutSeconds;

        /// <summary>
        /// Initialize AI Backend Service
        /// </summary>
        /// <param name="url">Backend URL (default: http://localhost:5000)</param>
        /// <param name="timeout">Timeout in seconds (default: 60)</param>
        public AIBackendService(string url = "http://localhost:5000", int timeout = 60)
        {
            backendUrl = url.TrimEnd('/');
            timeoutSeconds = timeout;

            // Create new HttpClient instance with proper timeout
            httpClient = new HttpClient();
            httpClient.Timeout = TimeSpan.FromSeconds(timeoutSeconds);
        }

        /// <summary>
        /// Check if the AI backend is healthy and running
        /// </summary>
        /// <returns>True if backend is healthy, false otherwise</returns>
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await httpClient.GetAsync($"{backendUrl}/health");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    var json = JObject.Parse(content);
                    return json["status"]?.ToString() == "healthy";
                }
                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Health check failed: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Get backend status information
        /// </summary>
        /// <returns>Status information as JSON object, or null if failed</returns>
        public async Task<JObject> GetStatusAsync()
        {
            try
            {
                var response = await httpClient.GetAsync($"{backendUrl}/status");
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    return JObject.Parse(content);
                }
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Status check failed: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Send a message to the AI backend and get a response with optional command
        /// </summary>
        /// <param name="message">User message</param>
        /// <param name="mode">Mode: "agent" or "ask"</param>
        /// <param name="model">AI model name</param>
        /// <param name="telemetry">Telemetry data (optional)</param>
        /// <returns>AIResponse object with text response and optional command</returns>
        public async Task<AIResponse> SendMessageAsync(
            string message, 
            string mode = "agent", 
            string model = "qwen2.5:3b",
            System.Collections.Generic.Dictionary<string, object> telemetry = null,
            System.Threading.CancellationToken cancellationToken = default)
        {
            try
            {
                // Prepare request payload
                var payload = new
                {
                    message = message,
                    mode = mode.ToLower(),
                    model = model,
                    telemetry = telemetry
                };

                var jsonContent = JsonConvert.SerializeObject(payload);
                var httpContent = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                // Send POST request to /chat endpoint with cancellation support
                var response = await httpClient.PostAsync($"{backendUrl}/chat", httpContent, cancellationToken);

                // Read response
                var responseContent = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    var json = JObject.Parse(responseContent);
                    
                    if (json["success"]?.ToObject<bool>() == true)
                    {
                        return new AIResponse
                        {
                            Success = true,
                            Response = json["response"]?.ToString() ?? "[No response from AI]",
                            Command = ParseCommand(json["command"]),
                            Error = null
                        };
                    }
                    else
                    {
                        var error = json["error"]?.ToString() ?? "Unknown error";
                        return new AIResponse
                        {
                            Success = false,
                            Response = null,
                            Command = null,
                            Error = error
                        };
                    }
                }
                else
                {
                    return new AIResponse
                    {
                        Success = false,
                        Response = null,
                        Command = null,
                        Error = $"Backend error: HTTP {(int)response.StatusCode}"
                    };
                }
            }
            catch (HttpRequestException ex)
            {
                return new AIResponse
                {
                    Success = false,
                    Response = null,
                    Command = null,
                    Error = "AI Backend not available. Please ensure the backend server is running."
                };
            }
            catch (TaskCanceledException ex)
            {
                return new AIResponse
                {
                    Success = false,
                    Response = null,
                    Command = null,
                    Error = "Request timed out. The AI backend may be processing a complex query."
                };
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending message: {ex.Message}");
                return new AIResponse
                {
                    Success = false,
                    Response = null,
                    Command = null,
                    Error = ex.Message
                };
            }
        }

        /// <summary>
        /// Parse command JSON from API response
        /// </summary>
        /// <param name="commandJson">Command JSON token</param>
        /// <returns>DroneCommand object or null if no command</returns>
        private DroneCommand ParseCommand(JToken commandJson)
        {
            if (commandJson == null || commandJson.Type == JTokenType.Null)
                return null;

            try
            {
                var command = new DroneCommand
                {
                    Type = commandJson["type"]?.ToString(),
                    Parameters = new System.Collections.Generic.Dictionary<string, object>()
                };

                // Parse parameters
                var paramsToken = commandJson["params"];
                if (paramsToken != null && paramsToken.Type == JTokenType.Object)
                {
                    foreach (var prop in ((JObject)paramsToken).Properties())
                    {
                        command.Parameters[prop.Name] = prop.Value.ToObject<object>();
                    }
                }

                return command;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error parsing command: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Test the connection to the backend
        /// </summary>
        /// <returns>Connection test result message</returns>
        public async Task<string> TestConnectionAsync()
        {
            try
            {
                var isHealthy = await CheckHealthAsync();
                if (isHealthy)
                {
                    var status = await GetStatusAsync();
                    if (status != null)
                    {
                        var model = status["model"]?.ToString() ?? "unknown";
                        var backend = status["backend"]?.ToString() ?? "unknown";
                        return $"✓ Connected to AI Backend\nModel: {model}\nBackend: {backend}";
                    }
                    return "✓ Backend is healthy";
                }
                return "✗ Backend is not responding";
            }
            catch (Exception ex)
            {
                return $"✗ Connection failed: {ex.Message}";
            }
        }
    }
}
