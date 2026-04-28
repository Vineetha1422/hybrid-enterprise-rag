import requests

class AnswerGenerator:

    def build_prompt(self, query: str, context_blocks: list) -> str:
        context_text = "\n\n".join(context_blocks)

        prompt = f"""You are an enterprise knowledge assistant.

Answer the question using ONLY the provided context.

If the context contains structured data (lists of tickets, employees, etc.),
preserve the exact IDs, names, and values in your answer — do not summarize them away.

When answering, cite your sources inline like this: (Source: filename, Section: section_name).
Use only the filename and section name — do not repeat the full bracket format from the context.
If multiple sources support the answer, cite all of them.
Do not add a closing note or summary about which sources were used — citations inline are sufficient.
Do not copy or repeat the context format tags like [Source:...] in your answer body.
Only use (Source: filename, Section: name) format for inline citations.

If the answer is not in the context, say:
"I do not have enough information to answer that."

    Context:
    {context_text}

    Question: {query}

    Answer:
    """
        return prompt

    def generate(self, query : str, context_blocks : list):
        prompt = self.build_prompt(query, context_blocks)

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120  # don't hang forever
            )
            response.raise_for_status()
            return {
                "prompt_used": prompt,
                "answer": response.json()["response"]
            }

        except requests.exceptions.ConnectionError:
            return {
                "prompt_used": prompt,
                "answer": "Could not connect to Ollama. Make sure it is running on localhost:11434."
            }
        except requests.exceptions.Timeout:
            return {
                "prompt_used": prompt,
                "answer": "Ollama request timed out. The model may be overloaded."
            }
        except Exception as e:
            return {
                "prompt_used": prompt,
                "answer": f"Unexpected error during generation: {str(e)}"
            }