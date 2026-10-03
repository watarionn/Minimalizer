"""P1 differentiable-renderer smoke: prove gradients reach existing geometry."""
import torch
import pydiffvg

pydiffvg.set_use_gpu(False)
WIDTH = HEIGHT = 64

def render(center: torch.Tensor, radius: torch.Tensor) -> torch.Tensor:
    ellipse = pydiffvg.Ellipse(radius=radius, center=center)
    group = pydiffvg.ShapeGroup(
        shape_ids=torch.tensor([0]),
        fill_color=torch.tensor([1.0, 1.0, 1.0, 1.0]),
    )
    args = pydiffvg.RenderFunction.serialize_scene(WIDTH, HEIGHT, [ellipse], [group])
    return pydiffvg.RenderFunction.apply(
        WIDTH, HEIGHT, 2, 2, 0, None, *args
    )[..., 3]

target_center = torch.tensor([38.0, 34.0])
target_radius = torch.tensor([10.0, 14.0])
with torch.no_grad():
    target = render(target_center, target_radius)

center = torch.tensor([28.0, 27.0], requires_grad=True)
radius = torch.tensor([8.0, 10.0], requires_grad=True)
optimizer = torch.optim.Adam([center, radius], lr=0.25)
initial_loss = None
first_gradient = None

for step in range(40):
    optimizer.zero_grad()
    loss = ((render(center, radius) - target) ** 2).mean()
    if initial_loss is None:
        initial_loss = loss.detach().item()
    loss.backward()
    if step == 0:
        first_gradient = (center.grad.detach().clone(), radius.grad.detach().clone())
    torch.nn.utils.clip_grad_norm_([center, radius], 1.0)
    optimizer.step()
    with torch.no_grad():
        center.clamp_(1.0, 63.0)
        radius.clamp_(1.0, 30.0)

final_loss = ((render(center, radius) - target) ** 2).mean().detach().item()
assert first_gradient is not None
assert all(torch.isfinite(gradient).all() for gradient in first_gradient)
assert final_loss < initial_loss
print(f"P1_DIFFVG_GRADIENT_PASS loss={initial_loss:.8f}->{final_loss:.8f}")
