import { GoogleGenAI } from "@google/genai";
import { Language } from '../types';

let genAI: GoogleGenAI | null = null;

const getAIClient = () => {
  if (!genAI) {
    if (!process.env.API_KEY) {
        console.error("API_KEY is missing");
        return null;
    }
    genAI = new GoogleGenAI({ apiKey: process.env.API_KEY });
  }
  return genAI;
};

export const analyzeDreamMeaning = async (text: string, language: Language): Promise<string> => {
  const ai = getAIClient();
  if (!ai) return language === 'zh' ? "错误：未配置 API 密钥。" : "Error: API Key not configured.";

  const prompt = language === 'zh' 
    ? `你是一个梦境解读者。我将提供一段某人的梦话录音转录。
       请简要分析它（最多3句话）。关注潜意识的感觉或创造性联想。
       风格要有些神秘感但又不失理智。
       
       梦话内容: "${text}"`
    : `You are a dream interpreter. I will provide a transcript of someone talking in their sleep. 
       Please analyze it briefly (max 3 sentences). Focus on potential subconscious feelings or creative associations.
       Be somewhat mystical but grounded.
       
       Sleep Talk Transcript: "${text}"`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    
    return response.text || (language === 'zh' ? "无法解读梦境。" : "Could not interpret dream.");
  } catch (error) {
    console.error("Gemini Analysis Error:", error);
    return language === 'zh' ? "分析数据失败，请重试。" : "Failed to analyze data. Please try again.";
  }
};

export const generateDreamImage = async (text: string): Promise<string | null> => {
  const ai = getAIClient();
  if (!ai) return null;

  // Enhance the prompt to make it more artistic and dream-like
  const enhancedPrompt = `A surreal, artistic, and dream-like digital painting interpretation of the following sleep talk: "${text}". Abstract, ethereal, moody lighting.`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: {
        parts: [{ text: enhancedPrompt }],
      },
      config: {
        imageConfig: {
          aspectRatio: "1:1",
        },
      },
    });

    for (const part of response.candidates?.[0]?.content?.parts || []) {
      if (part.inlineData) {
        const base64EncodeString: string = part.inlineData.data;
        return `data:image/png;base64,${base64EncodeString}`;
      }
    }
    return null;
  } catch (error) {
    console.error("Gemini Image Generation Error:", error);
    return null;
  }
};