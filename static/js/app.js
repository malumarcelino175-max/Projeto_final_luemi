// ---------- utilidades ----------
function getCookie(name) {
  const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return m ? decodeURIComponent(m.pop()) : "";
}

function brl(valor) {
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function toast(msg, tipo) {
  const box = document.getElementById("toasts");
  if (!box) return;
  const el = document.createElement("div");
  el.className = "toast" + (tipo === "error" ? " error" : "");
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// ---------- menu lateral (mobile) ----------
(function () {
  const burger = document.getElementById("burger");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("backdrop");
  if (!burger) return;
  const toggle = () => {
    sidebar.classList.toggle("open");
    backdrop.classList.toggle("show");
  };
  burger.addEventListener("click", toggle);
  backdrop.addEventListener("click", toggle);
})();

// ---------- carrinho ----------
async function atualizarCarrinho(slug, quantidade) {
  const resp = await fetch(window.URLS.atualizarCarrinho, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
    body: JSON.stringify({ slug, quantidade }),
  });
  if (!resp.ok) throw new Error("Falha ao atualizar o carrinho");
  const dados = await resp.json();
  const badge = document.getElementById("cart-badge");
  if (badge) {
    badge.textContent = dados.itens_total;
    badge.classList.toggle("hidden", dados.itens_total === 0);
  }
  return dados;
}

// Página de serviços: +/- e "Adicionar"
document.querySelectorAll("[data-produto]").forEach((card) => {
  const slug = card.dataset.produto;
  const campo = card.querySelector(".qtd");
  const set = async (valor) => {
    const dados = await atualizarCarrinho(slug, Math.max(0, valor));
    campo.textContent = dados.quantidade;
  };
  card.querySelector(".menos")?.addEventListener("click", () => set(Number(campo.textContent) - 1));
  card.querySelector(".mais")?.addEventListener("click", () => set(Number(campo.textContent) + 1));
  card.querySelector(".adicionar")?.addEventListener("click", async () => {
    await set(Math.max(1, Number(campo.textContent)));
    toast(card.dataset.nome + " adicionado ao orçamento");
  });
});

// Página do carrinho: alterar quantidade recarrega os totais
document.querySelectorAll("[data-linha]").forEach((linha) => {
  const slug = linha.dataset.linha;
  const campo = linha.querySelector(".qtd");
  const aplicar = async (valor) => {
    await atualizarCarrinho(slug, Math.max(0, valor));
    window.location.reload();
  };
  linha.querySelector(".menos")?.addEventListener("click", () => aplicar(Number(campo.textContent) - 1));
  linha.querySelector(".mais")?.addEventListener("click", () => aplicar(Number(campo.textContent) + 1));
  linha.querySelector(".remover")?.addEventListener("click", () => aplicar(0));
});

// ---------- formulário do evento ----------
(function () {
  const form = document.getElementById("form-evento");
  if (!form) return;
  const botao = form.querySelector("button[type=submit]");
  const validar = () => {
    const ok = [...form.querySelectorAll("input[required]")].every((i) => i.value.trim().length > 0);
    botao.disabled = !ok;
  };
  form.addEventListener("input", validar);
  validar();

  const dataInput = form.querySelector("input[type=date]");
  if (dataInput && !dataInput.min) dataInput.min = new Date().toISOString().slice(0, 10);
})();
