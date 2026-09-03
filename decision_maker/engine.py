import os
# Prevent Hugging Face transformers from loading TensorFlow to avoid protobuf version conflicts
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import torch
from sentence_transformers import SentenceTransformer, util
from handoff import InterviewOutput, DecisionOutput, DecisionRecommendation

class VectorEngine:
    """Singleton for local SentenceTransformer model to prevent memory leaks."""
    _instance = None
    _model = None
    _pos_anchor = None
    _neg_anchor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorEngine, cls).__new__(cls)
            cls._initialize_model()
        return cls._instance

    @classmethod
    def _initialize_model(cls):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        cls._model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        # Upgraded anchors to evaluate technical and leadership competence vs failure/toxicity
        cls._pos_anchor = cls._model.encode("Exceptional technical mastery, brilliant problem solving, outstanding leadership, successful and competent.")
        cls._neg_anchor = cls._model.encode("Toxic behavior, extreme arrogance, completely failed the technical assessment, defensive, incompetent and rejected.")

    def score_text_list(self, text_list: list[str]) -> float:
        if not text_list:
            return 0.0
            
        embeddings = self._model.encode(text_list)
        total_score = 0.0
        
        for emb in embeddings:
            sim_pos = util.cos_sim(emb, self._pos_anchor).item()
            sim_neg = util.cos_sim(emb, self._neg_anchor).item()
            total_score += ((sim_pos - sim_neg) * 2.0)
            
        return max(-1.0, min(1.0, total_score / len(text_list)))


class DecisionRanker:
    def __init__(self):
        self.vector_engine = VectorEngine()
        # Tuned perfectly to catch "extreme arrogance" but spare "slightly defensive"
        self.veto_threshold = -0.33  
        self.confidence_target = 0.85
        self.modifier_weight = 0.15  

    def evaluate(self, candidate: InterviewOutput) -> DecisionOutput:
        # 1. Base Disqualification
        if candidate.gate_status.upper() in ["REJECTED", "FAILED"]:
            return self._generate_rejection(candidate, "Hard Gate Rejected by Upstream Agent")

        # 2. Vector Qualitative Scoring
        raw_strength = self.vector_engine.score_text_list(candidate.strengths)
        raw_gap = self.vector_engine.score_text_list(candidate.remaining_gaps)
        raw_red_flag = self.vector_engine.score_text_list(candidate.behavioral_red_flags)

        # Categorical Enforcement:
        # A gap or red flag can NEVER yield a positive number.
        # A strength can NEVER yield a negative number.
        strength_score = max(0.0, raw_strength)
        gap_score = min(0.0, raw_gap)
        red_flag_score = min(0.0, raw_red_flag)

        # 3. Behavioral Veto Logic
        if red_flag_score <= self.veto_threshold:
            return self._generate_rejection(candidate, "Severe Behavioral Red Flag Detected")

        # 4. Mathematical Modifiers
        # Red flags that miss the veto are heavily penalized (1.5x)
        net_vector = strength_score + gap_score + (red_flag_score * 1.5)
        net_vector = max(-1.0, min(1.0, net_vector))
        
        q_modifier = 1.0 + (net_vector * self.modifier_weight)

        conf = candidate.evaluation_confidence
        c_penalty = 1.0 if conf >= self.confidence_target else (conf / self.confidence_target)
        penalty_applied = conf < self.confidence_target

        # 5. Final Calculation
        raw_final = (candidate.interview_score * q_modifier) * c_penalty
        final_score = max(0.0, min(100.0, raw_final))

        # 6. Routing Logic
        if final_score >= 75.0:
            rec = DecisionRecommendation.APPROVE
        elif final_score >= 65.0 or penalty_applied:
            rec = DecisionRecommendation.ESCALATE
        else:
            rec = DecisionRecommendation.REJECT

        return DecisionOutput(
            candidate_id=candidate.candidate_id,
            base_score=round(candidate.interview_score, 2),
            final_score=round(final_score, 2),
            recommendation=rec,
            veto_reason=None,
            ai_confidence_penalty_applied=penalty_applied,
            probing_questions="\n".join(candidate.probing_questions_for_manager)
        )

    def _generate_rejection(self, candidate: InterviewOutput, reason: str) -> DecisionOutput:
        return DecisionOutput(
            candidate_id=candidate.candidate_id,
            base_score=round(candidate.interview_score, 2),
            final_score=0.0,
            recommendation=DecisionRecommendation.REJECT,
            veto_reason=reason,
            ai_confidence_penalty_applied=False,
            probing_questions=""
        )
