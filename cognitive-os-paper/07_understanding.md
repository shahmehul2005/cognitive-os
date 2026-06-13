# Module: Understanding SPEC

The **Understanding** module sits between **Attention** and **Identity**. While Attention acts as a filter, and Identity acts as a strategic constraint filter, Understanding constructs the **Situational Mental Model** ($M_t$) of what is currently happening in the workspace.

---

## 1. Situational Mental Models

Raw signals passing the attention filter are often ambiguous (e.g., containing pronouns like "it", "this bug", "that release"). Understanding resolves these ambiguities before the reasoning phase.

```
                         Signal from Attention (with pronouns/noise)
                                             │
                                             ▼
                              Coreference & Entity Resolution
                                             │
                                             ▼
                                Intent & Sentiment Classifier
                                             │
                                             ▼
                              Situational Mental Model (M_t)
```

### 1.1 Resolution Vectors
- **Coreference Resolution**: Mapping pronouns ("it", "they", "the script") to specific nodes in the Workspace Graph (`skill_id`, `task_id`, `fact_id`) using temporal and semantic proximity.
- **Intent Categorisation**: Classifying the communicative intent of the human or agent:
  - `Inquiry`: Requesting information or validation.
  - `Instruction`: Direct task assignment.
  - `Objection`: Highlighting constraints or risks.
  - `Consensus`: Confirming decisions.

### 1.2 Situational Model Schema
```json
{
  "timestamp": "2026-06-13T12:06:00Z",
  "raw_text": "We need to fix it before pushing.",
  "resolved_entities": [
    {
      "pronoun": "it",
      "resolved_uri": "file:///c:/Users/user/Desktop/mem/cognitive-os-paper/03_memory.md",
      "type": "document"
    }
  ],
  "intent": "Instruction",
  "sentiment": "neutral_urgent",
  "active_contexts": ["workspace_mem_01"]
}
```

---

## 2. Cognitive Algorithms

### 2.1 Understand()
Translates raw attention signals into resolved mental models.

* **Inputs**:
  - `attention_event`: The Event dict that passed the attention filter.
  - `local_context`: The set of recently accessed graph nodes (active subgraph).
* **Output**:
  - `mental_model`: Resolved situational JSON dictionary.

```python
def Understand(attention_event, local_context):
    raw_text = attention_event["payload"].get("text", "")
    
    # 1. Resolve coreferences using temporal-semantic similarity
    resolved_text, resolved_entities = ResolveCoreferences(raw_text, local_context)
    
    # 2. Extract ontological entities
    entities = ExtractOntologicalEntities(resolved_text)
    
    # 3. Classify intent
    intent = ClassifyIntent(resolved_text)
    
    mental_model = {
        "timestamp": attention_event["timestamp"],
        "resolved_text": resolved_text,
        "entities": entities,
        "resolved_references": resolved_entities,
        "intent": intent,
        "source": attention_event["source"]
    }
    
    return mental_model
```

---

## 3. Success Metrics & Evaluation

To evaluate semantic accuracy, we measure the **Entity Resolution Precision** and **Intent Accuracy**.

### 3.1 Formulations

1. **Resolution Precision ($P_{\text{res}}$)**:
   $$P_{\text{res}} = \frac{|E_{\text{resolved\_correct}}|}{|E_{\text{resolved}}|}$$
   *Measures the proportion of pronouns and files resolved to the correct semantic targets.*

2. **Intent F1-Score ($F1_{\text{intent}}$)**:
   *Standard macro-averaged F1 score across the intent categories.*

### 3.2 Evaluation Protocol
- Weekly regression tests using $50$ human-labeled test sentences containing coreferences. The target bounds are $P_{\text{res}} \ge 0.96$ and $F1_{\text{intent}} \ge 0.94$. If the score drops, parameter recalibration is triggered.
