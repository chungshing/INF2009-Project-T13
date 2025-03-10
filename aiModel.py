import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import AutoPeftModelForCausalLM

# Path to the adapter and additional weights
path_to_adapter = "minicpm"


# Load the fine-tuned model with the LoRA adapter
model = AutoModelForCausalLM.from_pretrained(
    path_to_adapter,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model.to(device=device, dtype=torch.bfloat16)
model.eval()

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained(path_to_adapter, trust_remote_code=True)

def analyze_image(image_path, text_input, context=None, top_p=0.95, top_k=50, temperature=0.65, repetition_penalty=1.0, max_new_tokens=200):
    if 'model' not in globals():
        raise ValueError("Model not loaded correctly. Please check the model path and loading process.")

    # Load and preprocess the image if available
    if image_path:
        image = Image.open(image_path).convert('RGB')
    else:
        image = None

    if context is None:
        context = []

    # Ensure the first message is from the user
    if len(context) == 0 or context[0]['role'] != 'user':
        msgs = [{'role': 'user', 'content': text_input}]
    else:
        msgs = context + [{'role': 'user', 'content': text_input}]

    print(f'msgs: {msgs}')

    # Generate the response from the model
    res, new_context, _ = model.chat(
        image=image,
        msgs=msgs,
        context=None,  # No previous context to the model, msgs handle that
        tokenizer=tokenizer,
        sampling=True,
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        max_new_tokens=max_new_tokens
    )

    print(f'res: {res.strip()}')
    print(f'new context: {new_context}')

    return res.strip(), new_context
