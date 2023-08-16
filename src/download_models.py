# %%
import torch
import gradio as gr
from demucs.pretrained import get_model
from tqdm import tqdm

model_list = [
    "htdemucs",
    "htdemucs_ft",
    "htdemucs_6s",
    "mdx_extra",
    "mdx_extra_q",
]

for model_name in tqdm(model_list):
    get_model(model_name)
# %%
