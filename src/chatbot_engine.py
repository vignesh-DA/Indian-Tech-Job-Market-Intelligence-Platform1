"""
Chatbot Engine for Career Assistant
Uses NLP for intelligent intent detection + CSV data analysis
"""

import json
import re
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import google.generativeai as genai
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.data_loader import load_recent_jobs

class ChatbotEngine:
    def __init__(self):
        """Initialize the chatbot engine with NLP-based intent detection + CSV data"""
        # Google Gemini API configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Model configuration
        self.model_name = 'gemini-2.5-flash'
        
        # Load job data from CSV
        self.jobs_df = load_recent_jobs()
        self.data_available = len(self.jobs_df) > 0
        
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
                    logging.info(f"Trying CSV data analysis...")
                    # Try CSV data analysis first
                    csv_response = self.analyze_csv_data(intent, user_message, user_profile)
                    if csv_response:
                        bot_message = csv_response
                    else:
                        bot_message = self._generate_fallback_response(
                            intent, category, user_message, user_profile
                        )
            
            else:
                # No Gemini key available - try CSV analysis first
                logging.warning(f"⚠️ Gemini API not configured. Trying CSV analysis...")
                csv_response = self.analyze_csv_data(intent, user_message, user_profile)
                if csv_response:
                    bot_message = csv_response
                else:
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
        
        import random
        
        msg_lower = user_message.lower()
        role = user_profile.get('role', 'developer')
        exp = user_profile.get('experience', 'mid-level')
        location = user_profile.get('location', 'India')
        intent, category, _ = self.detect_intent(user_message, use_ai=False)
        
        # Varied opening phrases (different for each intent)
        openings = {
            'learning_roadmap': [
                "That's a smart approach to growth!",
                "Building a solid learning path is key to success.",
                "Let me guide you through a structured learning roadmap.",
                "Great question! Here's how to build your skills systematically."
            ],
            'career_goal': [
                "I love your ambition!",
                "Let's map out your career trajectory.",
                "Excellent question about your career growth!",
                "Planning ahead is always smart."
            ],
            'job_explanation': [
                "Let me break down this role for you.",
                "Great role choice! Here's what you need to know.",
                "That's an interesting career path.",
                "Let me explain what this position entails."
            ],
            'salary_info': [
                "Salary expectations are important!",
                "Let me share the real numbers with you.",
                "Here's what you can expect earning-wise.",
                "Great question about compensation!"
            ],
            'skill_trends': [
                "The tech landscape is changing fast!",
                "Here are the skills everyone's looking for right now.",
                "Let me share what's trending in tech.",
                "Here are the most in-demand skills today."
            ],
            'skill_assessment': [
                "Let's assess where you stand!",
                "Understanding your strengths is crucial.",
                "Here's how to evaluate your skill set.",
                "Let me help you identify your strengths and gaps."
            ],
            'company_info': [
                "Great question about companies!",
                "Let me share insights about that organization.",
                "Here's what you should know about that company.",
                "That's a solid company to target!"
            ]
        }
        
        # Intent-specific fallback responses
        if intent == 'learning_roadmap':
            opening = random.choice(openings.get('learning_roadmap', openings['learning_roadmap']))
            return f"""{opening}

For a structured learning path, you typically need:
• Foundation: Programming basics & data structures
• Core Skills: Python, SQL, statistics fundamentals
• Specialized: Machine learning libraries (scikit-learn, TensorFlow)
• Advanced: Deep learning, model optimization, deployment

Recommended resources:
📺 YouTube: Andrew Ng's Machine Learning course, StatQuest with Josh Starmer
📚 Courses: Coursera ML Specialization, Udacity ML Nanodegree
📖 Books: "Hands-On Machine Learning" by Aurélien Géron
🏆 Practice: Kaggle competitions for real-world experience

Timeline: Typically 6-12 months with consistent learning.

What area interests you most?"""
        
        elif intent == 'career_goal':
            opening = random.choice(openings.get('career_goal', openings['career_goal']))
            return f"""{opening}

Key considerations for your next role:
• Your current skills and experience level ({exp} as {role.title()})
• Target companies and their requirements
• Salary expectations and growth potential
• Learning gap between your skills and target role

For you in {location}:
📈 Quick wins (0-3 months): Senior positions, specialist roles
⏱️ Mid-term (3-6 months): Leadership, architecture positions
🎯 Long-term (6-12 months): Manager, technical lead, principal roles

What type of role are you targeting?"""
        
        elif intent == 'job_explanation':
            opening = random.choice(openings.get('job_explanation', openings['job_explanation']))
            return f"""{opening}

Typically, this role involves:
• Core responsibilities and daily tasks
• Required technical and soft skills
• Career progression and growth opportunities
• Typical company structure and reporting lines

For you as a {exp} {role.title()} in {location}:
💰 Expected salary range based on your profile
❓ Common interview questions and preparation
⭐ Required skills to stand out

Which aspect interests you most?"""
        
        elif intent == 'salary_info':
            opening = random.choice(openings.get('salary_info', openings['salary_info']))
            return f"""{opening}

For {role.title()} with {exp} experience in {location}:
💼 Entry-level: ₹3-6 LPA
🔧 Mid-level: ₹8-15 LPA
👔 Senior: ₹15-25 LPA
🏆 Lead/Manager: ₹20-40 LPA

Factors that influence salary:
🏢 Company size and funding stage
📊 Years of experience and expertise
🎓 Specialized skills (Cloud, AI/ML, DevOps)
💬 Negotiation and timing
📍 Location and remote work policies

Curious about a specific role?"""
        
        elif intent == 'skill_trends':
            opening = random.choice(openings.get('skill_trends', openings['skill_trends']))
            return f"""{opening}

🔥 HIGH DEMAND:
• Cloud: AWS, Azure, GCP
• AI/ML: Python, TensorFlow, PyTorch
• Backend: Java, Go, Node.js
• DevOps: Kubernetes, Docker, Terraform

🚀 EMERGING:
• Large Language Models (LLMs)
• Prompt Engineering
• Full-stack Cloud Development
• Data Engineering

⏳ EVERGREEN:
• System Design & Architecture
• Problem-solving & Algorithms
• Communication & Collaboration

Which skills match your goals?"""
        
        elif intent == 'skill_assessment':
            opening = random.choice(openings.get('skill_assessment', openings['skill_assessment']))
            return f"""{opening}

Your current profile:
• Role: {role.title()}
• Experience: {exp}
• Location: {location}

To assess your skills, consider:
✅ What you can do well RIGHT NOW
❌ What you struggle with
⏳ What you want to learn next
🎯 What market demands for your target role

Quick assessment tips:
1. Compare your skills against job postings
2. Identify the gap (2-3 months to close?)
3. Create a focused learning plan
4. Build a portfolio to showcase

What specific skills would you like to improve?"""
        
        # Default fallback - generic but varied
        default_openings = [
            "Great question!",
            "That's an interesting topic!",
            "Let me help with that.",
            "I've got some insights for you.",
            "That's a common question among professionals!",
            "Perfect timing for this question."
        ]
        opening = random.choice(default_openings)
        
        return f"""{opening}

I can help you with:

📊 SKILL ASSESSMENT - Analyze strengths, identify gaps
💼 JOB INSIGHTS - Understand roles, requirements, companies
🎯 CAREER GROWTH - Build roadmaps, plan progression
📈 MARKET DATA - Salary trends, hot skills, job market

YOUR PROFILE:
• Role: {role.title()}
• Experience: {exp}
• Location: {location}
• Opportunities: {user_profile.get('total_matched_jobs', 0)} matching jobs

🤔 TRY ASKING ME:
• "What skills do I need for data science?"
• "What's the salary for senior engineers?"
• "Which tech skills are trending now?"
• "How do I transition to backend development?"

What would be most helpful for you?"""
    def analyze_csv_data(self, intent: str, user_message: str, user_profile: Dict) -> str:
        """
        Analyze CSV job data to answer specific questions with real data
        
        Args:
            intent: Detected intent
            user_message: User's question
            user_profile: User's profile data
            
        Returns:
            Response with real data from CSV
        """
        if not self.data_available:
            return None
        
        from src.logger import logging
        
        try:
            msg_lower = user_message.lower()
            role = user_profile.get('role', '').lower()
            location = user_profile.get('location', 'India')
            
            # SALARY QUERIES
            if any(word in msg_lower for word in ['salary', 'salary', 'pay', 'compensation', 'earning', 'earn', 'wages']):
                return self._analyze_salary_data(role, location, user_profile)
            
            # SKILLS QUERIES
            elif any(word in msg_lower for word in ['skill', 'skills', 'competency', 'competencies', 'technologies']):
                return self._analyze_skills_data(role, location, user_profile)
            
            # COMPANY QUERIES
            elif any(word in msg_lower for word in ['company', 'companies', 'companies hiring', 'employers', 'firm', 'startup']):
                return self._analyze_company_data(role, location, user_profile)
            
            # JOB ROLE QUERIES
            elif any(word in msg_lower for word in ['data scientist', 'engineer', 'developer', 'analyst', 'role', 'job', 'position']):
                return self._analyze_role_data(role, user_message, user_profile)
            
            # LOCATION QUERIES
            elif any(word in msg_lower for word in ['location', 'city', 'remote', 'bangalore', 'delhi', 'mumbai', 'pune']):
                return self._analyze_location_data(user_message, user_profile)
            
        except Exception as e:
            logging.warning(f"⚠️ CSV analysis failed: {str(e)}")
            return None
        
        return None
    
    def _analyze_salary_data(self, role: str, location: str, user_profile: Dict) -> str:
        """Analyze salary data from CSV for specific role and location"""
        try:
            df = self.jobs_df.copy()
            
            # Filter by role if mentioned
            if role:
                df_filtered = df[df['title'].str.lower().str.contains(role, na=False)]
            else:
                df_filtered = df
            
            # Filter by location if mentioned
            if location and location.lower() != 'india':
                df_filtered = df_filtered[df_filtered['location'].str.lower().str.contains(location, na=False)]
            
            if len(df_filtered) == 0:
                return None
            
            # Extract salary data - try multiple column names
            salary_cols = [col for col in df.columns if 'salary' in col.lower()]
            if not salary_cols:
                return None
            
            salary_col = salary_cols[0]
            
            # Convert to numeric (handle different formats)
            df_filtered[salary_col] = pd.to_numeric(df_filtered[salary_col], errors='coerce')
            salaries = df_filtered[salary_col].dropna()
            
            if len(salaries) == 0:
                return None
            
            min_sal = salaries.quantile(0.25)
            avg_sal = salaries.mean()
            max_sal = salaries.quantile(0.75)
            median_sal = salaries.median()
            
            role_display = role.title() if role else "this role"
            
            response = f"""📊 **Salary Data for {role_display}** (Based on {len(df_filtered)} job postings)

Based on real job market data in {location}:

💰 **Salary Range:**
• Entry-level (25th percentile): ₹{min_sal:,.0f} LPA
• Average salary: ₹{avg_sal:,.0f} LPA
• Senior level (75th percentile): ₹{max_sal:,.0f} LPA
• Median: ₹{median_sal:,.0f} LPA

📈 **Data Insights:**
• Total job postings: {len(df_filtered)}
• Salary growth potential: ₹{max_sal - min_sal:,.0f} LPA
• Salary variation: High variation suggests skill-based pay

💡 **To Increase Your Salary:**
1. Gain specialized skills (AI/ML, Cloud, DevOps)
2. Switch to high-paying companies (big tech, fintech)
3. Negotiate based on this market data
4. Consider relocation to tier-1 cities

Would you like to know about specific skills that command higher salaries?"""
            
            return response
        
        except Exception as e:
            from src.logger import logging
            logging.warning(f"Salary analysis error: {str(e)}")
            return None
    
    def _analyze_skills_data(self, role: str, location: str, user_profile: Dict) -> str:
        """Analyze most in-demand skills from CSV"""
        try:
            df = self.jobs_df.copy()
            
            # Filter by role
            if role:
                df_filtered = df[df['title'].str.lower().str.contains(role, na=False)]
            else:
                df_filtered = df
            
            if len(df_filtered) == 0:
                return None
            
            # Find skills column
            skills_cols = [col for col in df.columns if 'skill' in col.lower()]
            if not skills_cols:
                return None
            
            skills_col = skills_cols[0]
            
            # Extract all skills and count them
            all_skills = []
            for skills_str in df_filtered[skills_col].dropna():
                if isinstance(skills_str, str):
                    # Split by comma or other delimiters
                    skills = [s.strip() for s in str(skills_str).split(',')]
                    all_skills.extend(skills)
            
            if not all_skills:
                return None
            
            # Count skill frequency
            from collections import Counter
            skill_counts = Counter(all_skills)
            top_skills = skill_counts.most_common(10)
            
            role_display = role.title() if role else "this field"
            
            skills_text = "\n".join([f"• **{skill}** - Required by {count} positions" 
                                     for skill, count in top_skills])
            
            response = f"""🎓 **Top Skills for {role_display}** (Based on {len(df_filtered)} jobs)

**Most In-Demand Skills:**

{skills_text}

📈 **Skill Trends:**
• {top_skills[0][0]} is the #1 requirement
• Python, SQL, and Cloud skills dominate
• AI/ML skills are emerging as critical

💼 **Your Strategy:**
1. Master the top 3 skills from above
2. Get certified in high-demand areas
3. Build portfolio projects using these skills
4. Learn from real job requirements

🚀 **Quick Win:**
Focus on **{top_skills[0][0]}** - it's the most in-demand skill right now!

Want to know how to learn any of these skills?"""
            
            return response
        
        except Exception as e:
            from src.logger import logging
            logging.warning(f"Skills analysis error: {str(e)}")
            return None
    
    def _analyze_company_data(self, role: str, location: str, user_profile: Dict) -> str:
        """Analyze top companies hiring from CSV"""
        try:
            df = self.jobs_df.copy()
            
            # Filter by location if specified
            if location and location.lower() != 'india':
                df_filtered = df[df['location'].str.lower().str.contains(location, na=False)]
            else:
                df_filtered = df
            
            if len(df_filtered) == 0:
                return None
            
            # Find company column
            company_cols = [col for col in df.columns if 'company' in col.lower()]
            if not company_cols:
                return None
            
            company_col = company_cols[0]
            
            # Get top companies
            from collections import Counter
            companies = df_filtered[company_col].dropna().value_counts().head(8)
            
            if len(companies) == 0:
                return None
            
            companies_text = "\n".join([f"• **{company}** - {count} open positions" 
                                        for company, count in companies.items()])
            
            response = f"""🏢 **Top Companies Hiring** (in {location})

**Most Active Recruiters:**

{companies_text}

📊 **Hiring Insights:**
• Total companies: {df_filtered[company_col].nunique()}
• Total open positions: {len(df_filtered)}
• Most active recruiter: {companies.index[0]} ({companies.iloc[0]} positions)

🎯 **Companies to Target:**
1. Big Tech (Microsoft, Google, Amazon, Meta, Apple)
2. High-growth startups (Better.com, Unacademy, Nykaa)
3. Fintech (PayTM, PhonePe, Razorpay)
4. Consulting (McKinsey, BCG, Deloitte)

💡 **Pro Tips:**
• Apply directly to company careers pages
• Network on LinkedIn with current employees
• Research company reviews on Glassdoor
• Prepare for company-specific interview rounds

Which company interests you most?"""
            
            return response
        
        except Exception as e:
            from src.logger import logging
            logging.warning(f"Company analysis error: {str(e)}")
            return None
    
    def _analyze_role_data(self, role: str, user_message: str, user_profile: Dict) -> str:
        """Analyze specific role data"""
        try:
            df = self.jobs_df.copy()
            
            # Find jobs matching the role
            role_keywords = user_message.lower().split()
            
            for keyword in role_keywords:
                if len(keyword) > 3:
                    matching_jobs = df[df['title'].str.lower().str.contains(keyword, na=False)]
                    if len(matching_jobs) > 5:
                        break
            
            if len(matching_jobs) < 5:
                return None
            
            # Analyze this role
            role_title = matching_jobs['title'].mode()[0] if len(matching_jobs) > 0 else "this role"
            
            response = f"""💼 **Role Analysis: {role_title}**

**Market Overview:**
• Total positions: {len(matching_jobs)}
• Active companies: {matching_jobs['company'].nunique() if 'company' in matching_jobs.columns else 'N/A'}

🎯 **This Role is Right For You If:**
• You have {user_profile.get('experience', 'relevant')} experience
• You live in {user_profile.get('location', 'India')} or are willing to relocate
• You want to grow as {role_title.lower()}

📊 **Next Steps:**
1. Check salary expectations for this role
2. Learn the required skills
3. Build a portfolio with relevant projects
4. Apply to top companies hiring for this role

Let me know if you want salary, skills, or company details!"""
            
            return response
        
        except Exception as e:
            from src.logger import logging
            logging.warning(f"Role analysis error: {str(e)}")
            return None
    
    def _analyze_location_data(self, user_message: str, user_profile: Dict) -> str:
        """Analyze location-based job market"""
        try:
            df = self.jobs_df.copy()
            
            # Find location mentioned
            locations = df['location'].unique() if 'location' in df.columns else []
            
            location_mentioned = None
            for loc in locations:
                if loc.lower() in user_message.lower():
                    location_mentioned = loc
                    break
            
            if not location_mentioned:
                return None
            
            df_loc = df[df['location'] == location_mentioned]
            
            response = f"""📍 **Job Market in {location_mentioned}**

**Market Size:**
• Total opportunities: {len(df_loc)}
• Companies hiring: {df_loc['company'].nunique() if 'company' in df_loc.columns else 'N/A'}

🏆 **Top Opportunities:**
• Data Science roles
• Software Engineering
• Product Management
• DevOps & Cloud

💰 **Salary Range (in {location_mentioned}):**
• Entry: ₹3-6 LPA
• Mid: ₹8-15 LPA
• Senior: ₹15-25 LPA

🎯 **Why {location_mentioned}?**
• Growing tech hub
• Competitive salaries
• Work culture and lifestyle

Want salary or skills details for {location_mentioned}?"""
            
            return response
        
        except Exception as e:
            from src.logger import logging
            logging.warning(f"Location analysis error: {str(e)}")
            return None