async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "API error");
  }
  return res.json();
}

function yen(value) {
  return new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY", maximumFractionDigits: 0 }).format(value);
}

async function loadSummary() {
  const data = await api("/api/dashboard/summary");
  const root = document.getElementById("summary");
  root.innerHTML = "";
  [
    ["商品総数", data.totalProducts],
    ["Embedding生成済み", data.embeddedProducts],
    ["未生成", data.missingEmbeddings],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "kpi-card";
    card.innerHTML = `<div class="label">${label}</div><div class="value">${value}</div>`;
    root.appendChild(card);
  });
}

async function loadProducts() {
  const state = document.getElementById("productsState");
  const tbody = document.querySelector("#productsTable tbody");
  state.textContent = "読込中...";
  tbody.innerHTML = "";

  try {
    const q = document.getElementById("productQuery").value.trim();
    const embeddingStatus = document.getElementById("embeddingStatus").value;
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (embeddingStatus) params.set("embeddingStatus", embeddingStatus);
    const data = await api(`/api/products?${params.toString()}`);
    if (!data.items.length) {
      state.textContent = "条件に一致する商品がありません。";
      return;
    }
    state.textContent = `${data.items.length}件表示`;
    data.items.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.productCode}</td>
        <td>${item.name}</td>
        <td>${item.category || "-"}</td>
        <td>${yen(item.price)}</td>
        <td>${item.embeddingStatus}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    state.textContent = `エラー: ${err.message}`;
  }
}

async function runSearch() {
  const state = document.getElementById("searchState");
  const tbody = document.querySelector("#searchTable tbody");
  state.textContent = "検索中...";
  tbody.innerHTML = "";
  try {
    const type = document.getElementById("queryType").value;
    const queryValue = document.getElementById("queryValue").value.trim();
    const topK = Number(document.getElementById("topK").value || 10);
    const scoreThreshold = Number(document.getElementById("threshold").value || 0);
    const payload = { type, topK, scoreThreshold };
    if (type === "product") payload.productId = Number(queryValue);
    else payload.text = queryValue;

    const data = await api("/api/similarity/search", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (!data.items.length) {
      state.textContent = "結果がありません。閾値を下げて再検索してください。";
      return;
    }
    state.textContent = `${data.items.length}件`;
    data.items.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.rank}</td>
        <td>${item.score.toFixed(4)}</td>
        <td>${item.productCode}</td>
        <td>${item.name}</td>
        <td>${item.category || "-"}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    state.textContent = `エラー: ${err.message}`;
  }
}

let currentJobId = null;
let pollTimer = null;

async function pollJob() {
  if (!currentJobId) return;
  try {
    const job = await api(`/api/embeddings/jobs/${currentJobId}`);
    document.getElementById("jobState").textContent =
      `status=${job.status}, progress=${Math.round(job.progress * 100)}%, success=${job.successCount}, fail=${job.failCount}`;
    if (job.status === "done" || job.status === "error") {
      clearInterval(pollTimer);
      pollTimer = null;
      await loadSummary();
      await loadProducts();
    }
  } catch (err) {
    document.getElementById("jobState").textContent = `エラー: ${err.message}`;
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function startEmbeddingJob() {
  const mode = document.getElementById("jobMode").value;
  const result = await api("/api/embeddings/jobs", {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
  currentJobId = result.jobId;
  document.getElementById("jobState").textContent = `job開始: ${currentJobId}`;
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollJob, 1500);
}

async function loadHealth() {
  try {
    const data = await api("/api/system/health");
    document.getElementById("health").textContent =
      `API=${data.api}, DB=${data.db}, pgvector=${data.pgvector}, checkedAt=${data.checkedAt}`;
  } catch (err) {
    document.getElementById("health").textContent = `エラー: ${err.message}`;
  }
}

document.getElementById("loadProductsBtn").addEventListener("click", loadProducts);
document.getElementById("runSearchBtn").addEventListener("click", runSearch);
document.getElementById("startJobBtn").addEventListener("click", () => {
  startEmbeddingJob().catch((err) => {
    document.getElementById("jobState").textContent = `エラー: ${err.message}`;
  });
});

const loadedViews = {
  dashboard: false,
  products: false,
  search: false,
  operations: false,
};

function getRoute() {
  const raw = window.location.hash.replace("#/", "").trim();
  if (["dashboard", "products", "search", "operations"].includes(raw)) {
    return raw;
  }
  return "dashboard";
}

async function loadRouteData(route) {
  if (loadedViews[route]) return;
  if (route === "dashboard") {
    await loadSummary();
    await loadHealth();
  } else if (route === "products") {
    await loadProducts();
  }
  loadedViews[route] = true;
}

async function renderRoute() {
  const route = getRoute();
  document.querySelectorAll("[data-route-view]").forEach((el) => {
    el.classList.toggle("active", el.getAttribute("data-route-view") === route);
  });
  document.querySelectorAll("[data-route-link]").forEach((el) => {
    const href = el.getAttribute("href") || "";
    el.classList.toggle("active", href === `#/${route}`);
  });
  await loadRouteData(route);
}

window.addEventListener("hashchange", () => {
  renderRoute().catch(() => {});
});

if (!window.location.hash) {
  window.location.hash = "#/dashboard";
}
renderRoute().catch(() => {});
