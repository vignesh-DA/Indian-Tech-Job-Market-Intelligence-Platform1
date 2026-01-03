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
from typing import Dict, List, Tuple, Any
from datetime import datetime

class ChatbotEngine:
    def __init__(self):
        """Initialize the chatbot engine with intent patterns"""
        self.intent_patterns = {
            # Category 1: User Profiling
            'skill_assessment': [
                r'assess.*skill', r'evaluate.*skill', r'skill.*strength', r'my.*skill',
                r'what.*skill.*have', r'analyze.*my.*profile', r'profile.*assessment'
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
                r'explain.*job', r'what.*role', r'job.*responsibilities', r'job.*requirement',
                r'understand.*job', r'tell.*about.*job', r'describe.*position'
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
                r'resource.*learn', r'course.*recommend', r'training.*plan'
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
        detected_category = 'general'
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = len(message_lower) / max(len(message_lower), 100)
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_intent = intent
                        detected_category = self._get_category(intent)
        
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

Job Market Data:
- Total opportunities available for this profile
- Salary insights and market trends
- High-demand skills in the region
- Career growth opportunities

Current Context:
- Answering questions about career development
- Providing personalized recommendations
- Based on Indian tech job market data
"""
        
        if recommendations:
            top_jobs = recommendations[:3]
            context += "\nTop Job Recommendations:\n"
            for i, job in enumerate(top_jobs, 1):
                context += f"{i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')} - {job.get('match_score', 0)}% match\n"
        
        return context
    
    def create_system_prompt(self) -> str:
        """Create system prompt for Gemini API"""
        return """You are an AI Career Assistant specialized in the Indian tech job market. Your role is to help professionals:

1. **User Profiling**: Assess skills, parse resumes, identify career goals
2. **Job Intelligence**: Explain job roles, compare opportunities, provide company insights
3. **Career Guidance**: Plan career progression, identify skill gaps, provide learning roadmaps
4. **Market Insights**: Share salary information, trending skills, market statistics

Guidelines:
- Be specific and actionable in your advice
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
                         gemini_api=None) -> Dict[str, Any]:
        """
        Generate chatbot response using Gemini API
        
        Args:
            user_message: User's question
            user_profile: User's profile data
            conversation_history: Previous messages
            recommendations: Current job recommendations
            gemini_api: Gemini API client (google.generativeai)
        
        Returns:
            Dict with response and metadata
        """
        # Detect intent
        intent, category, confidence = self.detect_intent(user_message)
        
        # Build context
        context = self.build_context(user_profile, recommendations)
        
        # Prepare conversation for API
        conversation = []
        for msg in conversation_history[-4:]:  # Keep last 4 messages for context
            conversation.append({
                'role': 'user' if msg['role'] == 'user' else 'model',
                'parts': [msg['content']]
            })
        
        # Add current message
        conversation.append({
            'role': 'user',
            'parts': [f"{context}\n\nUser Question: {user_message}"]
        })
        
        try:
            if gemini_api:
                # Use Gemini API
                model = gemini_api.GenerativeModel(
                    model_name='gemini-pro',
                    system_instruction=self.create_system_prompt()
                )
                
                # Send message to Gemini
                response = model.generate_content(
                    conversation[-1]['parts'][0],  # Just send current message
                    generation_config=gemini_api.types.GenerationConfig(
                        max_output_tokens=500,
                        temperature=0.7,
                    )
                )
                
                bot_message = response.text
            else:
                # Fallback: Generate contextual response without API
                bot_message = self._generate_fallback_response(
                    intent, category, user_message, user_profile
                )
            
            return {
                'success': True,
                'message': bot_message,
                'intent': intent,
                'category': category,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error generating response: {str(e)}',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_fallback_response(self, intent: str, category: str, 
                                   user_message: str, user_profile: Dict) -> str:
        """Generate fallback response when API is not available"""
        
        responses = {
            'skill_assessment': f"""Based on your profile as a {user_profile.get('role', 'developer')} with {user_profile.get('experience', 'experience')}:

Your Current Strengths:
- {', '.join(user_profile.get('skills', ['Technical knowledge'])[:3])}

Top Recommendations:
1. Deepen expertise in your primary skills
2. Learn complementary technologies
3. Build projects to showcase skills

Next Steps:
- Take online courses for skill enhancement
- Contribute to open-source projects
- Build a strong portfolio""",
            
            'career_goal': f"""Your Career Path Suggestions:

Current Level: {user_profile.get('experience', 'Mid-level')}

Potential Career Progressions:
1. Specialist Role - Deepen in current skills
2. Leadership Track - Move to team lead/manager
3. Architect Role - System design and strategy
4. Entrepreneurship - Start your own venture

Location: {user_profile.get('location', 'India')}
Market Demand: High for your profile

Recommended Timeline:
- 6 months: Build next skill
- 1 year: Consider role change
- 2-3 years: Senior/Lead position""",
            
            'job_explanation': """Job Role Breakdown:

Responsibilities:
- Design and development
- System optimization
- Team collaboration
- Code review and mentoring

Requirements:
- Core technical skills
- Problem-solving ability
- Communication skills
- Industry experience

Salary Range (India):
- Entry: ₹15-25 LPA
- Mid: ₹25-50 LPA
- Senior: ₹50+ LPA""",
            
            'salary_info': f"""Market Salary Insights for {user_profile.get('location', 'India')}:

Your Experience Level: {user_profile.get('experience', 'Not specified')}

Salary Ranges:
- Bangalore: ₹20-60 LPA
- Mumbai: ₹18-55 LPA
- Hyderabad: ₹18-50 LPA
- Pune: ₹16-45 LPA

Factors Affecting Salary:
- Years of experience
- Technical skills
- Company size/profile
- Location
- Negotiation skills""",
            
            'skill_trends': """Most Trending Skills (2026):

High Demand:
1. AI/Machine Learning
2. Cloud Technologies (AWS, Azure, GCP)
3. DevOps & Kubernetes
4. System Design
5. Full-stack Development

Emerging:
- Generative AI
- Web3 Technologies
- Advanced Data Engineering
- Cybersecurity

Learning Timeline:
- 3 months per skill
- 6 months to proficiency
- 1 year to expertise""",
            
            'learning_roadmap': f"""Learning Path for {user_profile.get('experience', 'your level')}:

Phase 1 (Months 1-2):
- Fundamentals and concepts
- Online courses and tutorials
- Small projects

Phase 2 (Months 3-4):
- Intermediate projects
- Real-world applications
- Peer review

Phase 3 (Months 5-6):
- Advanced topics
- Portfolio projects
- Job preparation

Resources:
- Udemy, Coursera, Pluralsight
- YouTube channels
- Documentation and blogs
- Open-source contributions""",
            
            'general': f"""Hello! I'm your Career Assistant. I can help you with:

📊 Skill Assessment - Analyze your strengths and gaps
💼 Job Intelligence - Understand roles and opportunities
🎯 Career Guidance - Plan your career path
📈 Market Insights - Salary trends and demand

Your Current Profile:
- Role: {user_profile.get('role', 'Not specified')}
- Experience: {user_profile.get('experience', 'Not specified')}
- Location: {user_profile.get('location', 'Not specified')}

What would you like to explore?"""
        }
        
        return responses.get(intent, responses['general'])
