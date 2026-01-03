"""
Chatbot Engine for Career Assistant
Handles 4 categories:
1. User Profiling (Skills Assessment, Resume Parser, Career Goal Detection)
2. Job Intelligence (Job Explanation, Job Comparison, Company Info)
3. Career Guidance (Career Path, Skill Gap, Learning Roadmap)
4. Market Insights (Salary Info, Skill Trends, Market Stats)
"""

import json
import re
import requests
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime

class ChatbotEngine:
    def __init__(self):
        """Initialize the chatbot engine with intent patterns"""
        # OpenRouter API configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = "google/gemini-3-flash-preview"  # Using Gemini 3 with reasoning
        self.intent_patterns = {
            # Category 1: User Profiling
            'skill_assessment': [
                r'assess.*skill', r'evaluate.*skill', r'skill.*strength', r'my.*skill',
                r'what.*skill.*have', r'analyze.*my.*profile', r'profile.*assessment',
                r'skill.*require', r'skill.*need', r'what.*skill.*[a-z]+', r'required.*skill'
            ],
            'resume_parser': [
                r'parse.*resume', r'upload.*resume', r'resume.*analysis', r'extract.*resume',
                r'analyze.*resume', r'my.*experience'
            ],
            'career_goal': [
                r'career.*goal', r'career.*path', r'what.*role.*suit', r'suitable.*role',
                r'next.*role', r'career.*aspiration', r'role.*recommendation'
            ],
            
            # Category 2: Job Intelligence
            'job_explanation': [
                r'explain.*job', r'what.*role', r'job.*responsib', r'job.*require',
                r'understand.*job', r'tell.*about.*job', r'describe.*position',
                r'role.*explain', r'what.*[a-z]+.*engineer', r'what.*[a-z]+.*developer',
                r'what.*data.*science', r'what.*job.*[a-z]+'
            ],
            'job_comparison': [
                r'compare.*job', r'compare.*role', r'difference.*job', r'which.*job.*better',
                r'vs\..*job', r'job.*vs\.', r'difference.*role'
            ],
            'company_info': [
                r'company.*info', r'about.*company', r'company.*culture', r'hiring.*company',
                r'company.*review', r'growth.*company', r'career.*company'
            ],
            
            # Category 3: Career Guidance
            'career_planning': [
                r'career.*planning', r'career.*progression', r'career.*trajectory',
                r'career.*roadmap', r'next.*step', r'plan.*career', r'progression.*path'
            ],
            'skill_gap': [
                r'skill.*gap', r'missing.*skill', r'lack.*skill', r'gap.*analysis',
                r'skill.*deficit', r'what.*need.*learn', r'learn.*skill'
            ],
            'learning_roadmap': [
                r'learning.*roadmap', r'learn.*course', r'learning.*path', r'how.*learn',
                r'resource.*learn', r'course.*recommend', r'training.*plan',
                r'step.*by.*step', r'python', r'guide.*learn', r'teach.*me'
            ],
            
            # Category 4: Market Insights
            'salary_info': [
                r'salary.*info', r'salary.*range', r'market.*salary', r'pay.*range',
                r'compensation', r'salary.*trend', r'how.*much.*earn'
            ],
            'skill_trends': [
                r'trending.*skill', r'in.*demand.*skill', r'hot.*skill', r'skill.*trend',
                r'popular.*skill', r'emerging.*tech'
            ],
            'market_stats': [
                r'market.*statistic', r'job.*statistic', r'market.*overview', r'job.*count',
                r'hiring.*trend', r'market.*demand'
            ]
        }
    
    def detect_intent(self, user_message: str) -> Tuple[str, str, float]:
        """
        Detect user intent from message
        Returns: (intent_name, category, confidence)
        """
        message_lower = user_message.lower()
        max_confidence = 0
        detected_intent = 'general'
        detected_category = 'General'
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Confidence based on pattern match quality
                    confidence = 0.8 + (0.2 * (len(match.group(0)) / len(message_lower)))
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_intent = intent
                        detected_category = self._get_category(intent)
        
        # If no pattern matched, return general with low confidence
        if detected_intent == 'general':
            max_confidence = 0.1
        
        return detected_intent, detected_category, max_confidence
    
    def _get_category(self, intent: str) -> str:
        """Map intent to category"""
        if intent in ['skill_assessment', 'resume_parser', 'career_goal']:
            return 'User Profiling'
        elif intent in ['job_explanation', 'job_comparison', 'company_info']:
            return 'Job Intelligence'
        elif intent in ['career_planning', 'skill_gap', 'learning_roadmap']:
            return 'Career Guidance'
        elif intent in ['salary_info', 'skill_trends', 'market_stats']:
            return 'Market Insights'
        return 'General'
    
    def build_context(self, user_profile: Dict[str, Any], recommendations: List[Dict] = None) -> str:
        """Build rich context string for Gemini API"""
        context = f"""
CAREER ASSISTANT CONTEXT:

User Profile:
- Current Role: {user_profile.get('role', 'Not specified')}
- Experience Level: {user_profile.get('experience', 'Not specified')}
- Location: {user_profile.get('location', 'Not specified')}
- Skills: {', '.join(user_profile.get('skills', [])[:10]) or 'Not specified'}
- Total Matched Jobs: {user_profile.get('total_matched_jobs', 0)}

"""
        
        if recommendations and len(recommendations) > 0:
            context += "Top Job Recommendations:\n"
            for i, job in enumerate(recommendations[:3], 1):
                context += f"{i}. {job.get('Job Title', 'N/A')} at {job.get('Company', 'N/A')}\n"
                context += f"   Location: {job.get('Location', 'N/A')}\n"
        
        return context
    
    def create_system_prompt(self) -> str:
        """Create system prompt for Gemini API"""
        return """You are an expert Career Assistant for tech professionals in India. Your role is to:

1. SKILL ASSESSMENT: Analyze technical skills, identify strengths and gaps
2. JOB INTELLIGENCE: Explain roles, compare positions, provide company insights
3. CAREER GUIDANCE: Create personalized career paths and learning roadmaps
4. MARKET INSIGHTS: Share salary data, trending skills, and market stats

Guidelines:
- Be conversational, helpful, and encouraging
- Provide actionable, specific advice
- Reference the user's current profile and skills
- Provide concrete examples from the Indian tech market
- Suggest learning resources when appropriate
- Keep responses concise but comprehensive
- Use bullet points for clarity
- Consider location-specific (India) salary and skill demands
- Focus on practical, achievable next steps

Always tailor advice to the user's current experience level and location."""
    
    def generate_response(self, user_message: str, user_profile: Dict, 
                         conversation_history: List[Dict], 
                         recommendations: List[Dict] = None,
                         use_openrouter: bool = True) -> Dict[str, Any]:
        """
        Generate chatbot response using OpenRouter API (Gemini 2.5 Flash)
        
        Args:
            user_message: User's question
            user_profile: User's profile data
            conversation_history: Previous messages
            recommendations: Current job recommendations
            use_openrouter: Whether to use OpenRouter API (True) or fallback (False)
        
        Returns:
            Dict with response and metadata
        """
        # Detect intent
        intent, category, confidence = self.detect_intent(user_message)
        
        # Build context
        context = self.build_context(user_profile, recommendations)
        
        # Prepare conversation for OpenRouter API (OpenAI-compatible format)
        messages = [
            {"role": "system", "content": self.create_system_prompt()},
            {"role": "system", "content": context}
        ]
        
        # Add conversation history (last 4 messages) - preserve reasoning_details if present
        for msg in conversation_history[-4:]:
            message_obj = {
                "role": "user" if msg['role'] == 'user' else "assistant",
                "content": msg['content']
            }
            # Preserve reasoning details from previous responses
            if msg['role'] == 'bot' and 'reasoning_details' in msg:
                message_obj['reasoning_details'] = msg['reasoning_details']
            messages.append(message_obj)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            if use_openrouter and self.openrouter_api_key:
                # Use OpenRouter API with Gemini 2.5 Flash
                headers = {
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "http://localhost:5000",  # Your app URL
                    "X-Title": "Career Assistant Chatbot",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "reasoning": {"enabled": True}  # Enable step-by-step reasoning for complex career questions
                }
                
                from src.logger import logging
                logging.info(f"🔹 Sending request to OpenRouter - Model: {self.model_name}")
                
                response = requests.post(
                    self.openrouter_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                logging.info(f"🔹 OpenRouter response: Status {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    message_data = result['choices'][0]['message']
                    bot_message = message_data.get('content', '')
                    reasoning_details = message_data.get('reasoning_details')  # Extract reasoning if present
                    logging.info(f"✅ AI response received: {bot_message[:100]}...")
                else:
                    # API error - log details and use fallback
                    logging.error(f"❌ OpenRouter API error: Status {response.status_code}")
                    logging.error(f"Response: {response.text}")
                    bot_message = self._generate_fallback_response(
                        intent, category, user_message, user_profile
                    )
                    bot_message = f"⚠️ API temporarily unavailable. Here's my response:\n\n{bot_message}"
            else:
                # No API key or API disabled - use fallback
                bot_message = self._generate_fallback_response(
                    intent, category, user_message, user_profile
                )
            
            response_data = {
                'success': True,
                'message': bot_message,
                'intent': intent,
                'category': category,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            # Include reasoning details if available (for conversation history)
            if 'reasoning_details' in locals():
                response_data['reasoning_details'] = reasoning_details
            return response_data
        
        except Exception as e:
            # Error - use fallback
            bot_message = self._generate_fallback_response(
                intent, category, user_message, user_profile
            )
            return {
                'success': True,
                'message': bot_message,
                'intent': intent,
                'category': category,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _generate_fallback_response(self, intent: str, category: str, 
                                   user_message: str, user_profile: Dict) -> str:
        """Generate smart fallback response that addresses the specific user question"""
        
        msg_lower = user_message.lower()
        role = user_profile.get('role', 'developer')
        exp = user_profile.get('experience', 'mid-level')
        location = user_profile.get('location', 'India')
        
        # Generic greeting/general response
        return f"""Hey! I'm your Career Assistant powered by AI!

Based on your question, I can help you with:

📊 **SKILL ASSESSMENT** - Analyze strengths, identify gaps
💼 **JOB INSIGHTS** - Understand roles, requirements, companies
🎯 **CAREER GROWTH** - Build roadmaps, plan progression
📈 **MARKET DATA** - Salary trends, hot skills, job market

YOUR PROFILE:
• Role: {role.title()}
• Experience: {exp}
• Location: {location}
• Opportunities: {user_profile.get('total_matched_jobs', 0)} matching jobs

💡 **ASK ME**:
• "What skills do I need for data science?"
• "What's the salary for senior engineers?"
• "Show me YouTube channels for learning ML"
• "How do I transition to backend development?"

What would be most helpful for you?"""
