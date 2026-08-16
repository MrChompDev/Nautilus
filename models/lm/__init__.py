"""Nautilus LM — custom, fully-local, from-scratch language models.

Each model is trained on CPU from a domain corpus, quantized to int8
(20-40MB), and served by a pure-NumPy inference engine with no runtime
dependency on torch or any cloud API.
"""
