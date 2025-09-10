"""
Answer summarization module using LLM
"""
import os
import json
from typing import List, Tuple, Any
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Expose last usage for metrics
LAST_SUMMARY_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def format_data_for_llm(rows: List[Tuple[Any, ...]]) -> str:
    """Format SQL results for LLM processing"""
    if not rows:
        return "No data found."
    
    # Convert rows to readable format
    formatted_data = []
    for i, row in enumerate(rows[:10]):  # Limit to first 10 rows
        if len(row) == 1 and isinstance(row[0], str):
            try:
                # Try to parse JSON data
                data = json.loads(row[0])
                formatted_data.append(f"Record {i+1}: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                formatted_data.append(f"Record {i+1}: {row[0]}")
        else:
            formatted_data.append(f"Record {i+1}: {row}")
    
    return "\n\n".join(formatted_data)


def summarize_results_with_llm(question: str, rows: List[Tuple[Any, ...]]) -> str:
    """Use LLM to generate meaningful answer from SQL results"""
    if not rows:
        return "Veritabanında bu soruya uygun veri bulunamadı."
    
    try:
        # Format data for LLM
        formatted_data = format_data_for_llm(rows)
        
        # Create prompt for LLM with better formatting
        prompt = f"""Sen bir tıbbi veritabanı uzmanısın. Kullanıcının sorusuna veritabanı sonuçlarına dayanarak düzenli ve anlamlı bir Türkçe cevap ver.

Kullanıcı Sorusu: {question}

Veritabanı Sonuçları:
{formatted_data}

Toplam {len(rows)} kayıt bulundu.

Lütfen cevabı şu formatta ver:
1. **Ana Cevap**: Kullanıcının sorusuna doğrudan cevap
2. **Detaylar**: Önemli sayısal veriler ve istatistikler
3. **Özet**: Genel değerlendirme

Cevap:"""

        # Call LLM
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen bir tıbbi veritabanı uzmanısın. Veritabanı sonuçlarını analiz edip kullanıcıya anlamlı cevaplar veriyorsun."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        # capture usage
        try:
            usage = response.usage
            if usage is not None:
                LAST_SUMMARY_USAGE.update({
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                })
        except Exception:
            pass

        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"LLM Error in summarization: {e}")
        return f"Veritabanında {len(rows)} kayıt bulunmaktadır. (LLM hatası: {str(e)})"


def summarize_results(question: str, rows: List[Tuple[Any, ...]]) -> str:
    """Main function to summarize results using LLM"""
    return summarize_results_with_llm(question, rows)
