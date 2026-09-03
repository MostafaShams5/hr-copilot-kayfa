"""CV Screening Agent - Core Logic"""

import json
import re
from pydantic_ai import Agent
from .config import settings

class ScreeningAgent:
    def __init__(self):
        self.agent = Agent(
            model=f"groq:{settings.LLM_MODEL}",
            system_prompt="You are an expert CV screener. Analyze CVs fairly and objectively. Always respond with valid JSON."
        )
    
    def screen_candidate(self, parsed_cv: dict, job: dict, candidate_id: str = None):
        """Screen a candidate against a job"""
        
        prompt = f"""
        Analyze this CV against the job requirement:
        
        CANDIDATE PROFILE:
        Name: {parsed_cv.get('name', 'Unknown')}
        Skills: {', '.join(parsed_cv.get('skills', []))}
        Experience: {parsed_cv.get('experience_years', 0)} years
        
        JOB REQUIREMENT:
        Role: {job.get('role', 'Unknown')}
        Required Skills: {', '.join(job.get('required_skills', []))}
        Min Experience: {job.get('min_years_experience', 0)} years
        
        Provide ONLY a JSON response with this exact format:
        {{
            "cv_score": <integer 0-100>,
            "recommendation": "PROCEED or REJECT",
            "strengths": [<list of strings>],
            "gaps": [<list of strings>],
            "reasoning": "<detailed explanation>"
        }}
        """
        
        try:
            import asyncio
            import concurrent.futures
            try:
                asyncio.get_running_loop()
                in_loop = True
            except RuntimeError:
                in_loop = False

            if in_loop:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    result = executor.submit(self.agent.run_sync, prompt).result()
            else:
                result = self.agent.run_sync(prompt)
            
            # Extract the response text
            # Try different ways to access the result
            response_text = None
            
            if hasattr(result, 'data'):
                response_text = result.data
            elif hasattr(result, 'output'):
                response_text = result.output
            elif hasattr(result, 'text'):
                response_text = result.text
            else:
                response_text = str(result)
            
            screening_result = self._parse_response(response_text)
        except Exception as e:
            print(f"Error during screening: {e}")
            screening_result = {
                "cv_score": 50,
                "recommendation": "REVIEW",
                "strengths": [],
                "gaps": [],
                "reasoning": f"Error during screening: {str(e)}"
            }
        
        return {
            "candidate_id": candidate_id or f"CAND-{parsed_cv.get('name', 'UNKNOWN').replace(' ', '-')}",
            "job_id": job.get("job_id", "JOB-UNKNOWN"),
            "cv_score": screening_result.get("cv_score", 50),
            "recommendation": screening_result.get("recommendation", "REVIEW"),
            "strengths": screening_result.get("strengths", []),
            "gaps": screening_result.get("gaps", []),
            "matched_skills": parsed_cv.get("skills", []),
            "reasoning": screening_result.get("reasoning", ""),
            "status": "SCREENED",
        }

    async def screen_candidate_async(self, parsed_cv: dict, job: dict, candidate_id: str = None) -> dict:
        """Asynchronously screen a parsed CV against job requirements using Groq LLM."""
        prompt = f"""
        You are an expert HR and Technical Recruiter. Analyze this candidate's CV against the job requirements.
        
        CANDIDATE CV DATA:
        Name: {parsed_cv.get('name', 'Unknown')}
        Email: {parsed_cv.get('email', 'Unknown')}
        Skills: {', '.join(parsed_cv.get('skills', []))}
        Experience: {json.dumps(parsed_cv.get('experience', []))}
        Education: {', '.join(parsed_cv.get('education', []))}
        
        JOB REQUIREMENT:
        Role: {job.get('role', 'Unknown')}
        Required Skills: {', '.join(job.get('required_skills', []))}
        Min Experience: {job.get('min_years_experience', 0)} years
        
        Provide ONLY a JSON response with this exact format:
        {{
            "cv_score": <integer 0-100>,
            "recommendation": "PROCEED or REJECT",
            "strengths": [<list of strings>],
            "gaps": [<list of strings>],
            "reasoning": "<detailed explanation>"
        }}
        """
        
        try:
            result = await self.agent.run(prompt)
            response_text = None
            if hasattr(result, 'data'):
                response_text = result.data
            elif hasattr(result, 'output'):
                response_text = result.output
            elif hasattr(result, 'text'):
                response_text = result.text
            else:
                response_text = str(result)
            
            screening_result = self._parse_response(response_text)
        except Exception as e:
            print(f"Error during async screening: {e}")
            screening_result = {
                "cv_score": 50,
                "recommendation": "REVIEW",
                "strengths": [],
                "gaps": [],
                "reasoning": f"Error during async screening: {str(e)}"
            }
        
        return {
            "candidate_id": candidate_id or f"CAND-{parsed_cv.get('name', 'UNKNOWN').replace(' ', '-')}",
            "job_id": job.get("job_id", "JOB-UNKNOWN"),
            "cv_score": screening_result.get("cv_score", 50),
            "recommendation": screening_result.get("recommendation", "REVIEW"),
            "strengths": screening_result.get("strengths", []),
            "gaps": screening_result.get("gaps", []),
            "matched_skills": parsed_cv.get("skills", []),
            "reasoning": screening_result.get("reasoning", ""),
            "status": "SCREENED",
        }
    
    def _parse_response(self, response_text):
        """Parse LLM JSON response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', str(response_text), re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return parsed
        except Exception as e:
            print(f"JSON parse error: {e}")
        
        # Fallback
        return {
            "cv_score": 50,
            "recommendation": "REVIEW",
            "strengths": [],
            "gaps": [],
            "reasoning": str(response_text)[:500] if response_text else "Unable to parse response"
        }
