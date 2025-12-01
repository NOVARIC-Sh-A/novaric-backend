import type { NextApiRequest, NextApiResponse } from 'next';
import { GoogleGenAI } from '@google/genai';
import OpenAI from 'openai';
import { supabase } from '../../lib/supabaseClient';

type ApiResponse = {
  chatgptReply?: string | null;
  geminiReply?: string | null;
  error?: string;
};

// -----------------------------
// LOG ACTIVITY TO SUPABASE
// -----------------------------
const logToSupabase = async (
  user_prompt: string,
  chatgpt_reply: string | null,
  gemini_reply: string | null,
  source_ip: string | string[] | undefined
) => {
  try {
    const { error } = await supabase.from('ai_lab_logs').insert({
      user_prompt,
      chatgpt_reply,
      gemini_reply,
      source_ip: Array.isArray(source_ip) ? source_ip[0] : source_ip,
    });

    if (error) {
      console.error('Supabase logging error:', error.message);
    }
  } catch (err) {
    console.error('Unexpected Supabase logging error:', err);
  }
};

// -----------------------------
// API ROUTE HANDLER
// -----------------------------
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).end('Method Not Allowed');
  }

  const { prompt } = req.body;

  if (!prompt || typeof prompt !== 'string') {
    return res.status(400).json({ error: 'Prompt is required and must be a string.' });
  }

  // Check API keys
  if (!process.env.GEMINI_API_KEY || !process.env.OPENAI_API_KEY) {
    return res.status(500).json({
      error: "API keys for AI services are not configured on the server.",
    });
  }

  try {
    // INIT BOTH CLIENTS
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

    // RUN BOTH MODELS IN PARALLEL
    const [geminiResult, chatgptResult] = await Promise.allSettled([
      ai.models.generateContent({
        model: 'gemini-3.0-pro',
        contents: [
          {
            role: "user",
            parts: [{ text: prompt }],
          },
        ],
      }),

      openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [{ role: 'user', content: prompt }],
      }),
    ]);

    // GEMINI RESPONSE
    const geminiReply =
      geminiResult.status === 'fulfilled'
        ? geminiResult.value.response.text()
        : null;

    // CHATGPT RESPONSE
    const chatgptReply =
      chatgptResult.status === 'fulfilled'
        ? chatgptResult.value.choices[0]?.message?.content ?? null
        : null;

    // LOG ERRORS
    if (geminiResult.status === 'rejected')
      console.error("Gemini API error:", geminiResult.reason);

    if (chatgptResult.status === 'rejected')
      console.error("ChatGPT API error:", chatgptResult.reason);

    // ASYNC LOGGING TO SUPABASE
    const source_ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    logToSupabase(prompt, chatgptReply, geminiReply, source_ip);

    // RETURN BOTH RESPONSES
    return res.status(200).json({ geminiReply, chatgptReply });

  } catch (error) {
    console.error('Error in /api/dual-ai:', error);
    return res.status(500).json({ error: 'An internal server error occurred.' });
  }
}
