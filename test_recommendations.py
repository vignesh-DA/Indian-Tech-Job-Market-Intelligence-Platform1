#!/usr/bin/env python
"""Test the recommendation engine"""

from src.recommendation_engine import JobRecommendationEngine
from src.data_loader import load_recent_jobs

# Load jobs
jobs_df = load_recent_jobs(days=30)
print(f'Jobs loaded: {len(jobs_df)} rows')

# Train engine
engine = JobRecommendationEngine()
engine.train(jobs_df)

# Test recommendation
user_profile = {
    'skills': ['Python', 'Django'],
    'role': 'Software Engineer',
    'experience': '2-4 years',
    'location': 'Bangalore'
}

results = engine.calculate_match(user_profile, top_n=5)
print(f'Recommendations: {len(results)} rows')
print(f'Match scores range: {results["match_score"].min():.2f} - {results["match_score"].max():.2f}')

if len(results) > 0:
    for idx, row in results.head(3).iterrows():
        print(f'\n{row["title"]} at {row["company"]}')
        print(f'  Match Score: {row["match_score"]:.2f}%')
        print(f'  Skills: {row["skills"][:50]}...')
else:
    print('No recommendations found!')
