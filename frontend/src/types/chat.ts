export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface QueryRequest {
  query: string;
}

export interface QueryResponse {
  response: string;
}

export interface SchemeInfo {
  id: string;
  name: string;
  description: string;
  risk: "Very High" | "High" | "Moderate" | "Low";
  riskColor: "error" | "tertiary" | "secondary";
  riskIcon: string;
  path: string;
}
