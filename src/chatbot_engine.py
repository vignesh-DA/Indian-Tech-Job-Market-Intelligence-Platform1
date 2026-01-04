"""
Chatbot Engine for Career Assistant
Uses NLP for intelligent intent detection
"""

import json
import re
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import google.generativeai as genai
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ChatbotEngine:
    def __init__(self):
        """Initialize the chatbot engine with NLP-based intent detection"""
        # Google Gemini API configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Model configuration
        self.model_name = 'gemini-2.5-flash'
        
        # Intent training data - examples for each intent
        self.intent_training_data = {
            'skill_assessment': [
                "assess my skills", "evaluate my capabilities", "what are my strengths",
                "identify my skill gaps", "analyze my competencies", "what skills do I have",
                "rate my technical abilities", "how strong am i in python", "evaluate my backend skills"
            ],
            'resume_parser': [
                "parse my resume", "analyze my experience", "extract resume information",
                "review my background", "evaluate my work history", "assess my experience level"
            ],
            'career_goal': [
                "what role suits me", "suitable career for me", "what should be my next role",
                "career aspirations", "role recommendations", "what career path is good for me",
                "am i suitable for data science"
            ],
            'job_explanation': [
                "explain this job", "what does this role involve", "job responsibilities",
                "job requirements", "describe the position", "tell me about this job",
                "what does a backend developer do", "what is a data scientist", "role details"
            ],
            'job_comparison': [
                "compare these jobs", "difference between roles", "which job is better",
                "compare positions", "frontend vs backend", "role comparison", "which is better job"
            ],
            'company_info': [
                "company information", "about this company", "company culture", "company review",
                "hiring at company", "company growth", "working at company"
            ],
            'career_planning': [
                "career planning", "career progression", "career roadmap", "career trajectory",
                "next steps in career", "plan my progression", "how to advance in career"
            ],
            'skill_gap': [
                "skill gaps", "missing skills", "what skills to learn", "skill deficit",
                "gaps in my knowledge", "what do i need to learn", "lack of skills"
            ],
            'learning_roadmap': [
                "learning roadmap", "how to learn", "learning path", "step by step guide",
                "course recommendations", "learning resources", "teach me python",
                "how do i start", "youtube links for learning", "training plan", "beginner guide"
            ],
            'salary_info': [
                "salary information", "salary range", "market salary", "compensation",
                "how much do i earn", "pay range", "salary trends", "how much salary"
            ],
            'skill_trends': [
                "trending skills", "in demand skills", "popular skills", "skill trends",
                "hot technologies", "emerging skills", "which skills are trending"
            ],
            'market_stats': [
                "market statistics", "job statistics", "market overview", "hiring trends",
                "job market", "market demand", "how many jobs", "job availability"
            ],
            'general': [
                "hello", "hi", "hey", "thanks", "thank you", "okay", "yes", "no", "bye",
                "what can you do", "who are you", "help", "hello there"
            ]
        }
        
        # Build TF-IDF vectorizer
        self._build_nlp_vectorizer()
    
    def humanize_ai_text(self, text: str) -> str:
        """
        Transform AI-generated text into warm, human-readable content using NLP.
        
        Transformations:
        - Remove markdown formatting (**, *, _, etc)
        - Formal → conversational tone
        - Long paragraphs → short, scannable chunks (2-3 sentences)
        - Replace bullet variations with consistent • bullets
        - Add empathy markers and contractions
        - Replace jargon with simple language
        - Strategic whitespace for breathing room
        
        Returns text that feels human, not robotic.
        """
        
        # 0. STANDARDIZE BULLET POINTS FIRST (before markdown removal)
        # This prevents "* **Text**" from losing its bullet indicator
        lines = text.split('\n')
        standardized_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Convert various bullet formats to •
            if stripped.startswith(('- ', '* ', '+ ')):
                # Get everything after the bullet
                content = stripped[2:].strip()
                # Preserve leading whitespace, replace bullet with •
                indent = len(line) - len(line.lstrip())
                standardized_lines.append(' ' * indent + '• ' + content)
            elif stripped.startswith('•'):
                standardized_lines.append(line)
            else:
                standardized_lines.append(line)
        
        text = '\n'.join(standardized_lines)
        
        # 1. REMOVE MARKDOWN FORMATTING - STRICT ORDER TO PREVENT DOUBLE MARKUP
        # First remove bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # Remove strikethrough (~~text~~) before single asterisks
        text = re.sub(r'~~(.+?)~~', r'\1', text)
        
        # Remove italic - single asterisks on both sides (but not double)
        # Use non-greedy matching and word boundaries to catch *word* pattern
        text = re.sub(r'\*([^*]+?)\*', r'\1', text)
        
        # Remove underscores used for italics/bold (_text_ or __text__)
        text = re.sub(r'_([^_]+?)_', r'\1', text)
        
        # 3. Convert formal phrases to conversational
        conversational_map = {
            r"I am here to": "I'm here to",
            r"I would recommend": "I'd recommend",
            r"you should consider": "you might want to consider",
            r"it is important": "it's important",
            r"you are required": "you'll need",
            r"in order to": "to",
            r"with regard to": "about",
            r"in addition": "plus",
            r"furthermore": "also",
            r"consequently": "so",
            r"therefore": "that's why",
            r"however": "but",
            r"as well as": "and",
            r"in my opinion": "I think",
            r"I recommend": "I'd recommend",
        }
        
        for formal, conversational in conversational_map.items():
            text = re.sub(formal, conversational, text, flags=re.IGNORECASE)
        
        # 3. Convert formal phrases to conversational
        conversational_map = {
            r"I am here to": "I'm here to",
            r"I would recommend": "I'd recommend",
            r"you should consider": "you might want to consider",
            r"it is important": "it's important",
            r"you are required": "you'll need",
            r"in order to": "to",
            r"with regard to": "about",
            r"in addition": "plus",
            r"furthermore": "also",
            r"consequently": "so",
            r"therefore": "that's why",
            r"however": "but",
            r"as well as": "and",
            r"in my opinion": "I think",
            r"I recommend": "I'd recommend",
        }
        
        for formal, conversational in conversational_map.items():
            text = re.sub(formal, conversational, text, flags=re.IGNORECASE)
        
        # 4. Break long paragraphs into shorter ones (but preserve bullet lists)
        paragraphs = text.split('\n\n')
        new_paragraphs = []
        
        for para in paragraphs:
            # Skip bullet point lists - they should stay as-is
            if para.strip().startswith('•') or '\n•' in para:
                new_paragraphs.append(para)
                continue
                
            # If paragraph is very long (>300 chars), split it intelligently
            if len(para) > 300:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                chunk = []
                
                for sentence in sentences:
                    chunk.append(sentence)
                    if len(chunk) >= 2:  # 2-3 sentence chunks
                        new_paragraphs.append(' '.join(chunk))
                        chunk = []
                if chunk:
                    new_paragraphs.append(' '.join(chunk))
            else:
                new_paragraphs.append(para)
        
        text = '\n\n'.join(new_paragraphs)
        
        # 5. Add empathy markers where appropriate
        if 'help' in text.lower() and "I'm here" in text:
            if "back" not in text.lower():
                text = text.replace("I'm here", "I'm here to have your back,")
        
        # 6. Remove overly formal conclusion phrases
        text = re.sub(r'\bLet me know if you need any clarification\b', "Feel free to ask if anything's unclear", text, flags=re.IGNORECASE)
        text = re.sub(r'\bDo not hesitate to\b', 'Feel free to', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPlease feel free to\b', 'Feel free to', text, flags=re.IGNORECASE)
        
        # 7. Add warmth to key phrases
        text = re.sub(r'\byou can\b', "you'll be able to", text, flags=re.IGNORECASE)
        text = re.sub(r'\bI suggest\b', "I'd suggest", text, flags=re.IGNORECASE)
        text = re.sub(r'\byou need to\b', "you'll want to", text, flags=re.IGNORECASE)
        
        # 8. Clean up multiple spaces and excessive punctuation
        text = re.sub(r' {2,}', ' ', text)  # Remove multiple spaces
        text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive line breaks
        text = re.sub(r'([.!?]){2,}', r'\1', text)  # Remove multiple punctuation
        
        return text.strip()
    
    def _build_nlp_vectorizer(self):
        """Build TF-IDF vectorizer for intent matching"""
        # Flatten all training data
        all_texts = []
        self.intent_labels = []
        
        for intent, examples in self.intent_training_data.items():
            for example in examples:
                all_texts.append(example)
                self.intent_labels.append(intent)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=500
        )
        
        # Fit vectorizer on training data
        self.intent_vectors = self.vectorizer.fit_transform(all_texts)
    
    def detect_intent(self, user_message: str, use_ai: bool = False) -> Tuple[str, str, float]:
        """
        Detect user intent using NLP semantic similarity (primary)
        Falls back to AI (Gemini) only if explicitly requested
        Returns: (intent_name, category, confidence)
        
        NOTE: AI intent detection is disabled by default due to API quota limits.
        Use NLP-based semantic similarity instead for faster, offline intent detection.
        """
        from src.logger import logging
        
        # Use NLP-based detection as primary method (reliable, fast, no API calls)
        nlp_intent, nlp_category, nlp_confidence = self._detect_intent_nlp(user_message)
        
        # Only try AI if:
        # 1. Explicitly requested with use_ai=True, AND
        # 2. NLP confidence is low (< 0.4), AND
        # 3. Gemini API key is available
        if use_ai and nlp_confidence < 0.4 and self.gemini_api_key:
            try:
                logging.info(f"ℹ️ NLP confidence low ({nlp_confidence:.2f}), trying AI intent detection...")
                return self._detect_intent_ai(user_message, logging)
            except Exception as e:
                logging.warning(f"⚠️ AI intent detection failed: {str(e)}. Using NLP result.")
                return nlp_intent, nlp_category, nlp_confidence
        
        # Return NLP result
        return nlp_intent, nlp_category, nlp_confidence
    
    def _detect_intent_ai(self, user_message: str, logging) -> Tuple[str, str, float]:
        """
        Use Google Gemini API to detect intent with AI understanding
        """
        intent_prompt = f"""Analyze this user message and detect their intent for a career guidance chatbot.

User Message: "{user_message}"

Available intents:
1. skill_assessment - Asking about assessing or evaluating skills, strengths, capabilities
2. resume_parser - Asking about resume analysis or experience evaluation  
3. career_goal - Asking about suitable roles, career aspirations, or goal suggestions
4. job_explanation - Asking to explain job roles, responsibilities, requirements
5. job_comparison - Comparing different job roles or positions
6. company_info - Asking about company information or culture
7. career_planning - Asking about career progression, roadmap, or planning
8. skill_gap - Asking about missing skills or areas to improve
9. learning_roadmap - Asking how to learn, course recommendations, step-by-step guidance
10. salary_info - Asking about salary ranges, compensation, or pay
11. skill_trends - Asking about trending skills, hot skills, or market demands
12. market_stats - Asking about job statistics, hiring trends, or market overview
13. general - General greeting or unclear intent

Respond ONLY with valid JSON format (no markdown):
{{"intent": "intent_name", "confidence": 0.95}}"""
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(intent_prompt)
            result = json.loads(response.text)
            
            detected_intent = result.get('intent', 'general')
            confidence = result.get('confidence', 0.5)
            
            # Validate intent
            all_intents = list(self.intent_training_data.keys())
            if detected_intent not in all_intents:
                detected_intent = 'general'
                confidence = 0.1
            
            detected_category = self._get_category(detected_intent)
            logging.info(f"🧠 AI Intent: {detected_intent} (confidence: {confidence:.2f})")
            
            return detected_intent, detected_category, confidence
        
        except Exception as e:
            logging.error(f"❌ AI intent detection error: {str(e)}")
            raise
    
    def _detect_intent_nlp(self, user_message: str) -> Tuple[str, str, float]:
        """
        NLP-based intent detection using semantic similarity (TF-IDF + Cosine Similarity)
        This understands natural language without rigid patterns
        """
        # Vectorize user message
        user_vector = self.vectorizer.transform([user_message])
        
        # Calculate cosine similarity with all training examples
        similarities = cosine_similarity(user_vector, self.intent_vectors)[0]
        
        # Get the best matching intent
        best_idx = np.argmax(similarities)
        best_similarity = float(similarities[best_idx])
        best_intent = self.intent_labels[best_idx]
        
        # Confidence threshold - if very low similarity, might be general
        if best_similarity < 0.15:
            detected_intent = 'general'
            confidence = 0.2
        else:
            detected_intent = best_intent
            # Convert similarity score (0-1) to confidence
            confidence = min(0.95, best_similarity * 1.2)  # Scale and cap at 0.95
        
        detected_category = self._get_category(detected_intent)
        
        return detected_intent, detected_category, confidence
    
    def _get_category(self, intent: str) -> str:
        """Map intent to category"""
        category_map = {
            'skill_assessment': 'User Profiling',
            'resume_parser': 'User Profiling',
            'career_goal': 'User Profiling',
            'job_explanation': 'Job Intelligence',
            'job_comparison': 'Job Intelligence',
            'company_info': 'Job Intelligence',
            'career_planning': 'Career Guidance',
            'skill_gap': 'Career Guidance',
            'learning_roadmap': 'Career Guidance',
            'salary_info': 'Market Insights',
            'skill_trends': 'Market Insights',
            'market_stats': 'Market Insights',
            'general': 'General'
        }
        return category_map.get(intent, 'General')
    
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

FORMATTING RULES (IMPORTANT):
• Use bullet points (•) instead of asterisks or dashes for all lists
• Structure responses with clear headings using plain text (no markdown symbols)
• Keep paragraphs short (2-3 lines maximum)
• Use numbered lists (1. 2. 3.) only for step-by-step processes
• Add blank lines between sections for readability
• NO asterisks, NO bold text (**), NO underscores
• Keep formatting simple and clean

Content Guidelines:
• Be conversational, helpful, and encouraging
• Provide actionable, specific advice
• Reference the user's current profile and skills
• Provide concrete examples from the Indian tech market

WHEN USERS ASK FOR LEARNING RESOURCES:
• Include RELEVANT LINKS and URLs for learning resources
• Suggest popular platforms like YouTube, Coursera, Udemy, FreeCodeCamp, official documentation
• Provide both free and paid resource options when applicable
• Include direct links when recommending specific courses or channels
• Format links clearly with the resource name followed by URL in parentheses
• Example: Corey Schadafer Python Course (https://www.youtube.com/c/Coreyms)

Additional Tips:
• Keep responses concise but comprehensive
• Always use bullet points for lists and options
• Consider location-specific (India) salary and skill demands
• Focus on practical, achievable next steps
• Break complex information into digestible chunks

Always tailor advice to the user's current experience level and location."""
    
    def generate_response(self, user_message: str, user_profile: Dict, 
                         conversation_history: List[Dict], 
                         recommendations: List[Dict] = None,
                         use_gemini: bool = True) -> Dict[str, Any]:
        """
        Generate chatbot response using Google Gemini API
        
        Args:
            user_message: User's question
            user_profile: User's profile data
            conversation_history: Previous messages
            recommendations: Current job recommendations
            use_gemini: Whether to use Gemini API (True) or fallback (False)
        
        Returns:
            Dict with response and metadata
        """
        from src.logger import logging
        
        # Detect intent
        intent, category, confidence = self.detect_intent(user_message)
        
        # Build context
        context = self.build_context(user_profile, recommendations)
        
        try:
            # Try Google Gemini API first if key available
            if use_gemini and self.gemini_api_key:
                logging.info(f"🔹 Attempting Google Gemini API - Model: {self.model_name}")
                
                try:
                    # Configure Gemini API
                    genai.configure(api_key=self.gemini_api_key)
                    
                    # Create the model instance
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=self.create_system_prompt()
                    )
                    
                    # Build the full prompt with context and history
                    history_text = ""
                    if conversation_history:
                        history_text = "\n\nRecent conversation:\n"
                        for msg in conversation_history[-3:]:  # Last 3 messages for context
                            role = "You" if msg.get('role') == 'user' else "Assistant"
                            history_text += f"{role}: {msg.get('content', '')}\n"
                    
                    full_prompt = f"""{context}{history_text}

Current Question: {user_message}

Provide a helpful, specific response focused on career growth and skill development."""
                    
                    # Generate response
                    response = model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=500,
                            temperature=0.7,
                            top_p=0.9,
                            top_k=40
                        )
                    )
                    
                    bot_message = response.text
                    # Apply humanization for warm, readable output
                    bot_message = self.humanize_ai_text(bot_message)
                    logging.info(f"✅ Google Gemini API response received: {bot_message[:100]}...")
                    
                except Exception as gemini_error:
                    logging.warning(f"⚠️ Google Gemini API failed: {str(gemini_error)}")
                    logging.info(f"Using fallback response...")
                    bot_message = self._generate_fallback_response(
                        intent, category, user_message, user_profile
                    )
            
            else:
                # No Gemini key available - use fallback
                logging.warning(f"⚠️ Gemini API not configured. Using fallback response.")
                bot_message = self._generate_fallback_response(
                    intent, category, user_message, user_profile
                )
            
            # Apply humanization to ensure consistent friendly tone
            bot_message = self.humanize_ai_text(bot_message)
            
            response_data = {
                'success': True,
                'message': bot_message,
                'intent': intent,
                'category': category,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            return response_data
        
        except Exception as e:
            # Final fallback for any unexpected errors
            logging.error(f"❌ Unexpected error in generate_response: {str(e)}")
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
        """Generate smart fallback response that addresses the specific user intent"""
        
        msg_lower = user_message.lower()
        role = user_profile.get('role', 'developer')
        exp = user_profile.get('experience', 'mid-level')
        location = user_profile.get('location', 'India')
        intent, category, _ = self.detect_intent(user_message, use_ai=False)
        
        # Intent-specific fallback responses
        if intent == 'learning_roadmap':
            return f"""Great! Let me help you build a learning roadmap.

For a structured learning path, you typically need:
• Foundation: Programming basics & data structures
• Core Skills: Python, SQL, statistics fundamentals
• Specialized: Machine learning libraries (scikit-learn, TensorFlow)
• Advanced: Deep learning, model optimization, deployment

Recommended resources:
• YouTube: Andrew Ng's Machine Learning course, StatQuest with Josh Starmer
• Courses: Coursera ML Specialization, Udacity ML Nanodegree
• Books: "Hands-On Machine Learning" by Aurélien Géron
• Practice: Kaggle competitions for real-world experience

Timeline: Typically 6-12 months with consistent learning.

What specific area would you like to focus on first?"""
        
        elif intent == 'career_goal':
            return f"""Excellent! Let me help you plan your career direction.

Key considerations for your next role:
• Your current skills and experience level
• Target companies and their requirements
• Salary expectations and growth potential
• Learning gap between your skills and target role

For {role.title()} with {exp} experience in {location}:
• Immediate opportunities (0-3 months): Senior positions, specialist roles
• Mid-term (3-6 months): Leadership, architecture positions
• Long-term (6-12 months): Manager, technical lead, principal roles

What type of role are you targeting? Tell me more about your goals!"""
        
        elif intent == 'job_explanation':
            return f"""Let me explain this role for you.

Typically, this role involves:
• Core responsibilities and daily tasks
• Required technical and soft skills
• Career progression and growth opportunities
• Typical company structure and reporting lines

For you as a {exp} {role.title()} in {location}:
• Expected salary range based on your profile
• Common interview questions and preparation
• Required skills to stand out

Which specific aspect would you like to know more about?"""
        
        elif intent == 'salary_info':
            return f"""Let me share some salary insights for {location}.

For {role.title()} with {exp} experience:
• Entry-level: ₹3-6 LPA
• Mid-level: ₹8-15 LPA
• Senior: ₹15-25 LPA
• Lead/Manager: ₹20-40 LPA

Factors that influence salary:
• Company size and funding stage
• Years of experience and expertise
• Specialized skills (Cloud, AI/ML, DevOps)
• Negotiation and timing
• Location and remote work policies

What specific role or skill area interests you?"""
        
        elif intent == 'skill_trends':
            return f"""Here are the hottest skills right now in {location}:

HIGH DEMAND:
• Cloud: AWS, Azure, GCP
• AI/ML: Python, TensorFlow, PyTorch
• Backend: Java, Go, Node.js
• DevOps: Kubernetes, Docker, Terraform

EMERGING:
• Large Language Models (LLMs)
• Prompt Engineering
• Full-stack Cloud Development
• Data Engineering

EVERGREEN:
• System Design & Architecture
• Problem-solving & Algorithms
• Communication & Collaboration

Which skills match your career goals?"""
        
        # Default fallback - generic greeting
        return f"""Hey! I'm your Career Assistant powered by AI!

Based on your question, I can help you with:

SKILL ASSESSMENT - Analyze strengths, identify gaps
JOB INSIGHTS - Understand roles, requirements, companies
CAREER GROWTH - Build roadmaps, plan progression
MARKET DATA - Salary trends, hot skills, job market

YOUR PROFILE:
• Role: {role.title()}
• Experience: {exp}
• Location: {location}
• Opportunities: {user_profile.get('total_matched_jobs', 0)} matching jobs

ASK ME:
• "What skills do I need for data science?"
• "What's the salary for senior engineers?"
• "Show me YouTube channels for learning ML"
• "How do I transition to backend development?"

What would be most helpful for you?"""
