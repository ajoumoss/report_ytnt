import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def summarize_transcript(transcript, title):
    """
    Summarizes the provided transcript using Google Gemini API.
    """
    if not transcript:
        return "No transcript available for summarization."
    
    # Use Gemini 2.5 Pro for higher quality and detail
    # Note: If 2.5 Pro is not available, fallback to 2.0 Flash or Pro might be needed, 
    # but based on debug output, 2.5 Pro is listed (models/gemini-2.5-pro).
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    prompt = f"""
    Analyze the following YouTube video transcript and specificially classify its political stance and summarize its content.

    **Video Title:** {title}
    **Transcript:**
    {transcript[:30000]}

    **Political Context (CRITICAL - CURRENT YEAR 2026):**
    - **Current President**: Lee Jae-myung (Democratic Party).
    - **Ruling Party**: Democratic Party of Korea (DP).
    - **Opposition Party**: People Power Party (PPP).
    - **PPP Leader**: Jang Dong-hyeok (장동혁). He is the current leader of the Conservatives.
    - **Han Dong-hoon**: He has been **EXPELLED** (제명) from the PPP. He is NOT the leader anymore. Do not classify pro-PPP content as "Pro-Han" unless it specifically supports Han Dong-hoon *against* the current PPP leadership.
    - **Common Stance**: "Pro-Jang" (Pro-Jang Dong-hyeok) is the mainstream Conservative stance.

    **Instructions:**
    1.  **Title Translation**: If the video title is in English, provide a natural Korean translation. If it is already in Korean, use the original title. Return this as `korean_title`.

    2.  **Political Classification**: Classify the video's stance based on the **2026 Context** above.
        - **IMPORTANT**: If the video discusses ANY current events, elections, government policy, or political figures (Lee Jae-myung, Yoon Suk-yeol, Han Dong-hoon, Jang Dong-hyeok), it **MUST** be classified as `is_political: true`. Use `false` ONLY for completely non-political content (e.g., cooking, gaming, pure entertainment without social commentary).
        - Format: **"Broad Category - Specific Faction"**
        - Broad Categories: `진보` (Progressive) or `보수` (Conservative).
        - Specific Factions:
            - Progressive: `친이재명` (Pro-Lee Jae-myung), `반윤석열` (Anti-Yoon), etc.
            - Conservative: `친장동훈` (Pro-Jang Dong-hyeok), `친윤석열` (Pro-Yoon), `반이재명` (Anti-Lee).
            - **Note**: Only use `친한동훈` (Pro-Han) if the content explicitly supports Han Dong-hoon *over* the current PPP leadership.
        - Example: `진보 - 친이재명`, `보수 - 친장동혁`.

    3.  **Cast & Key Messages**: Identify the **Host** and **Guests/Panelists**.
        - For EVERY person identified (Host included), provide:
            - `name`: Name of the person.
            - `key_message`: A 1-sentence summary of their specific argument or stance in this video.
        - **Requirement**: Must include at least the Host.

    4.  **Summary**: Provide a comprehensive summary of the video. 
        - **Do NOT** use a separate section header for "Political Leaning Analysis". 
        - Instead, integrate any analysis into the natural flow of the summary or key points.
        - Use **### [Header]** style for sections. Recommended sections:
            - **### [핵심 주제]**
            - **### [상세 내용]**
            - **### [결론 및 시사점]**

    5.  **Formatting**: Ensure excellent readability. Use **bullet points** for lists and **double newlines** between paragraphs to avoid dense text blocks.

    6.  **Output Format**: Return a JSON object with the following fields:
        - `is_political`: boolean (true if political/social, else false)
        - `korean_title`: string (Translated title or original)
        - `classification`: string (e.g., "진보 - 친이재명")
        - `cast`: array of objects, each containing:
            - `name`: string (Name of the person)
            - `key_message`: string (Their key message)
        - `summary`: string (Markdown formatted summary)

    **Response (JSON only):**
    """
    
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Debug: Print raw response to see why it fails
        # print(f"DEBUG LLM Response for {title}: {text_response[:100]}...") 
        
        # Clean up JSON if it has markdown formatting
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        import json
        result = json.loads(text_response)
        
        # Add usage metadata if available
        if hasattr(response, 'usage_metadata'):
             result['token_usage'] = {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'candidate_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            }
        return result
    except Exception as e:
        print(f"LLM Error for {title}: {e}")
        return {"is_political": False, "summary": f"Error during summarization: {e}", "political_leaning": "Error", "analysis_failed": True}

def summarize_video(video_file, title):
    """
    Summarizes the video using Gemini 2.5 Pro (Multimodal).
    video_file: A Google GenAI File object.
    """
    print(f"  Analyzing video content (Multimodal): {title}...")
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    prompt = f"""
    Analyze the provided video and specificially classify its political stance and summarize its content.
    
    **Video Title:** {title}

    **Political Context (CRITICAL - CURRENT YEAR 2026):**
    - **Current President**: Lee Jae-myung (Democratic Party).
    - **Ruling Party**: Democratic Party of Korea (DP).
    - **Opposition Party**: People Power Party (PPP).
    - **PPP Leader**: Jang Dong-hyeok (장동혁). He is the current leader of the Conservatives.
    - **Han Dong-hoon**: He has been **EXPELLED** (제명) from the PPP. He is NOT the leader anymore. Do not classify pro-PPP content as "Pro-Han" unless it specifically supports Han Dong-hoon *against* the current PPP leadership.
    - **Common Stance**: "Pro-Jang" (Pro-Jang Dong-hyeok) is the mainstream Conservative stance.

    **Instructions:**
    1.  **Title Translation**: If the video title is in English, provide a natural Korean translation. If it is already in Korean, use the original title. Return this as `korean_title`.

    2.  **Political Classification**: Classify the video's stance based on the **2026 Context** above.
        - **IMPORTANT**: If the video discusses ANY current events, elections, government policy, or political figures (Lee Jae-myung, Yoon Suk-yeol, Han Dong-hoon, Jang Dong-hyeok), it **MUST** be classified as `is_political: true`. Use `false` ONLY for completely non-political content (e.g., cooking, gaming, pure entertainment without social commentary).
        - Format: **"Broad Category - Specific Faction"**
        - Broad Categories: `진보` (Progressive) or `보수` (Conservative).
        - Specific Factions:
            - Progressive: `친이재명` (Pro-Lee Jae-myung), `반윤석열` (Anti-Yoon), etc.
            - Conservative: `친장동훈` (Pro-Jang Dong-hyeok), `친윤석열` (Pro-Yoon), `반이재명` (Anti-Lee).
            - **Note**: Only use `친한동훈` (Pro-Han) if the content explicitly supports Han Dong-hoon *over* the current PPP leadership.
        - Example: `진보 - 친이재명`, `보수 - 친장동혁`.

    3.  **Cast & Key Messages**: Identify the **Host** and **Guests/Panelists** based on visual and audio cues.
        - For EVERY person identified (Host included), provide:
            - `name`: Name of the person.
            - `key_message`: A 1-sentence summary of their specific argument or stance in this video.
        - **Requirement**: Must include at least the Host.

    4.  **Summary**: Provide a comprehensive summary of the video. 
        - **Do NOT** use a separate section header for "Political Leaning Analysis". 
        - Instead, integrate any analysis into the natural flow of the summary or key points.
        - Use **### [Header]** style for sections. Recommended sections:
            - **### [핵심 주제]**
            - **### [상세 내용]**
            - **### [결론 및 시사점]**

    5.  **Output Format**: Return a JSON object with the following fields:
        - `is_political`: boolean (true if political/social, else false)
        - `korean_title`: string (Translated title or original)
        - `classification`: string (e.g., "진보 - 친이재명")
        - `cast`: array of objects, each containing:
            - `name`: string (Name of the person)
            - `key_message`: string (Their key message)
        - `summary`: string (Markdown formatted summary)

    **Response (JSON only):**
    """
    
    try:
        # Pass the video file *and* the prompt
        response = model.generate_content([video_file, prompt])
        text_response = response.text.strip()
        
        # Clean up JSON if it has markdown formatting
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        import json
        result = json.loads(text_response)

        # Add usage metadata if available
        if hasattr(response, 'usage_metadata'):
             result['token_usage'] = {
                'prompt_tokens': response.usage_metadata.prompt_token_count,
                'candidate_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count
            }
        return result
    
    except Exception as e:
        print(f"LLM Multimodal Error for {title}: {e}")
        return {"is_political": False, "summary": f"Error during multimodal summarization: {e}", "political_leaning": "Error", "analysis_failed": True}

if __name__ == "__main__":
    # Test
    title = "Test Video"
    transcript = "This is a test transcript about politics. The speaker argues that X is good and Y is bad."
    print(summarize_transcript(transcript, title))
