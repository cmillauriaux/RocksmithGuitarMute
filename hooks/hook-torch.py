
# Hook personnalisé pour exclure des modules PyTorch non essentiels
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Exclure des sous-modules PyTorch volumineux
excludedimports = [
    "torch.nn.modules.activation",
    "torch.nn.modules.batchnorm", 
    "torch.nn.modules.conv",
    "torch.nn.modules.dropout",
    "torch.nn.modules.linear",
    "torch.nn.modules.pooling",
    "torch.nn.modules.rnn",
    "torch.nn.modules.transformer",
    "torch.optim",
    "torch.cuda.amp",
    "torch.jit",
    "torch.distributed",
    "torch.multiprocessing",
    "torch.utils.tensorboard",
    "torch.utils.benchmark",
    "torch.profiler",
    "torch.fx",
    "torch.onnx",
    "torch.quantization",
    "torch.autograd.profiler",
]
