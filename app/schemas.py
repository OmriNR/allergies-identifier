from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str = Field(description="Server-assigned document ID.", examples=["a9fe1308fd014b7f8341c17cf97a0088"])
    filename: str = Field(description="Original uploaded filename.", examples=["allergen_reference.txt"])
    content_type: str = Field(description="MIME type as reported by the upload.", examples=["text/plain"])
    chunk_count: int = Field(description="Number of chunks the document was split into.", examples=[3])
    created_at: datetime = Field(description="When the document was ingested (UTC).")


class DocumentUploadResponse(BaseModel):
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]


class SearchQuery(BaseModel):
    query: str = Field(
        min_length=1,
        description="Free-text semantic search query.",
        examples=["milk protein synonyms casein whey"],
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of chunks to return.")
    document_id: str | None = Field(
        default=None, description="Restrict the search to a single document, if provided."
    )


class SearchResult(BaseModel):
    text: str = Field(description="The matched chunk's text.")
    score: float = Field(description="Cosine similarity score in [0, 1]; higher is more relevant.")
    document_id: str
    filename: str
    chunk_index: int = Field(description="Position of this chunk within its source document.")


class SearchResponse(BaseModel):
    results: list[SearchResult]


class AllergyCheckRequest(BaseModel):
    patient_allergies: list[str] = Field(
        min_length=1,
        description="The patient's known allergies, in plain language.",
        examples=[["peanuts", "shellfish"]],
    )
    ingredients_text: str | None = Field(
        default=None,
        description="Raw ingredients list to analyze. Required unless you're relying "
        "purely on retrieved reference documents.",
        examples=["water, peanut butter, soy sauce, natural flavors, spices"],
    )
    product_name: str | None = Field(
        default=None, description="Optional product name, used as extra context.", examples=["Thai Peanut Sauce"]
    )
    use_documents: bool = Field(
        default=True,
        description="Whether to retrieve supporting context (allergen synonyms, "
        "cross-reactivity notes) from ingested documents.",
    )
    document_ids: list[str] | None = Field(
        default=None, description="Restrict retrieval to these document IDs. Omit to search all ingested documents."
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Max number of retrieved chunks to use as context.")


class AllergenMatch(BaseModel):
    allergen: str = Field(description="The patient allergy this match corresponds to.")
    matched_term: str = Field(description="The specific ingredient/term that triggered the match.")
    confidence: Literal["high", "medium", "low"]
    evidence: str = Field(description="Why the model flagged this — quotes or paraphrases the source text.")


class NotificationPayload(BaseModel):
    title: str = Field(description="Short, patient-facing alert title.")
    message: str = Field(description="Patient-facing explanation and recommended action.")
    severity: Literal["none", "caution", "danger"]


class SourceRef(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    excerpt: str = Field(description="First ~280 characters of the retrieved chunk used as context.")


class AllergyCheckResponse(BaseModel):
    risk_level: Literal["none", "possible", "confirmed"]
    is_safe: bool = Field(description="Convenience flag: false whenever risk_level is not \"none\".")
    matches: list[AllergenMatch]
    notification: NotificationPayload
    reasoning_summary: str = Field(description="Short explanation of how the model reached its conclusion.")
    sources: list[SourceRef] = Field(description="Retrieved document chunks used as supporting context, if any.")
    cached: bool = Field(default=False, description="True if this response was served from the response cache.")
