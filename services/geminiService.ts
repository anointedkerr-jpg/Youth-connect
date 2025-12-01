import { GoogleGenAI, Type, Schema } from "@google/genai";
import { GeneratedResponse, PlanningItem } from "../types";

// Initialize Gemini
// NOTE: process.env.API_KEY is injected by the environment.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const modelId = "gemini-2.5-flash";

const planningItemSchema: Schema = {
  type: Type.OBJECT,
  properties: {
    title: { type: Type.STRING },
    description: { type: Type.STRING },
    materialsNeeded: {
      type: Type.ARRAY,
      items: { type: Type.STRING },
      description: "List of physical items or digital tools needed."
    },
    steps: {
      type: Type.ARRAY,
      items: { type: Type.STRING },
      description: "Actionable steps from planning to execution."
    },
    scriptureReference: { type: Type.STRING, description: "Relevant Bible verse(s)." },
    suggestedDuration: { type: Type.STRING, description: "e.g., '30 mins', '2 hours'" },
    difficultyLevel: { type: Type.STRING, enum: ["Low", "Medium", "High"] },
    estimatedCost: { type: Type.STRING, enum: ["Free", "Low", "Medium", "High"] },
    roles: { 
      type: Type.ARRAY, 
      items: { type: Type.STRING }, 
      description: "Suggested roles for the executive team (e.g., 'Worship Leader', 'Logistics')" 
    },
    assignedTeamMembers: {
      type: Type.ARRAY,
      items: { type: Type.STRING },
      description: "Specific names of team members assigned to this plan, if provided in context."
    }
  },
  required: ["title", "description", "materialsNeeded", "steps", "scriptureReference", "suggestedDuration", "difficultyLevel", "estimatedCost"],
};

const responseSchema: Schema = {
  type: Type.OBJECT,
  properties: {
    items: {
      type: Type.ARRAY,
      items: planningItemSchema,
    },
  },
  required: ["items"],
};

const SYSTEM_INSTRUCTION = `
You are an expert Youth Ministry Consultant for "YouthConnect", designed for a small Christian youth department (5-8 exec members) in Jamaica.
Your goal is to help them plan, grow, and execute events.

CRITICAL CONTEXT:
1. JAMAICAN CONTEXT: Recommendations must be realistic for Jamaican youth. Use local terminology where appropriate (e.g., "Lyme", "Reasoning", "Grounding"). Avoid heavy Americanisms (e.g., avoid prom, snow, thanksgiving, expensive camps).
2. SMALL TEAM: The team is small. Suggestions must be manageable for 5-8 leaders.
3. BUDGET CONSCIOUS: Prioritize low/no-cost ideas.
4. SPIRITUALLY DEEP: Activities should be fun but always have a spiritual anchor.
5. ENGAGING: Focus on getting youth OFF phones or using phones for engagement, not distraction.

Output MUST be valid JSON adhering to the schema provided.
`;

export const generateContent = async (prompt: string): Promise<PlanningItem[]> => {
  try {
    const response = await ai.models.generateContent({
      model: modelId,
      contents: prompt,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json",
        responseSchema: responseSchema,
        temperature: 0.7, // Creativity balance
      },
    });

    if (response.text) {
      const parsed: GeneratedResponse = JSON.parse(response.text);
      return parsed.items;
    }
    return [];
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
};

export const generateTextContent = async (prompt: string): Promise<string> => {
  try {
    // We use a lighter instruction for text content to ensure flexibility
    // and explicitly do NOT enforce JSON schema or MIME type here.
    const textSystemInstruction = `
    You are an expert Youth Ministry Consultant for "YouthConnect" in Jamaica.
    Provide creative, engaging, and culturally relevant content for youth ministry promotion.
    Keep the tone appropriate for Christian youth (Gen Z).
    `;

    const response = await ai.models.generateContent({
      model: modelId,
      contents: prompt,
      config: {
        systemInstruction: textSystemInstruction,
        temperature: 0.8,
      },
    });

    return response.text || "";
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
};
