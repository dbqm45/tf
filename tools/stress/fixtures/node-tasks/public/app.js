// Browser client.
async function load() {
  const tasks = await (await fetch("/api/tasks")).json();
  const ul = document.getElementById("list");
  ul.innerHTML = "";
  for (const t of tasks) {
    const li = document.createElement("li");
    li.textContent = t.title;
    li.className = (t.done ? "done " : "") + t.priority;
    li.onclick = async () => { await fetch(`/api/tasks/${t.id}/toggle`, { method: "POST" }); load(); };
    ul.appendChild(li);
  }
}
document.getElementById("add").onsubmit = async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value;
  const priority = document.getElementById("priority").value;
  await fetch("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, priority }) });
  document.getElementById("title").value = "";
  load();
};
load();
