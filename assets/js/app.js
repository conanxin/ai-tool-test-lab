fetch('data/cases.json')
  .then(r => r.json())
  .then(data => {
    const container = document.getElementById('case-list');
    if (!data.cases || data.cases.length === 0) {
      container.innerHTML = '<p style="color:var(--muted)">暂无案例</p>';
      return;
    }
    container.innerHTML = data.cases.map(c => `
      <article class="case-card">
        <h3><a href="${c.path}">${c.title}</a></h3>
        <div class="case-meta">
          <span class="tag status">${c.status}</span>
          <span class="tag type">${c.category}</span>
          <span class="tag phase">${c.phase}</span>
        </div>
        <div class="case-desc">
          <p><strong>本地角色：</strong>${c.local_role}</p>
          <p><strong>云端角色：</strong>${c.cloud_role}</p>
          ${c.summary ? `<p class="summary">${c.summary}</p>` : ""}
        </div>
      </article>
    `).join('');
  })
  .catch(err => {
    document.getElementById('case-list').innerHTML =
      '<p style="color:var(--muted)">加载案例失败：' + err.message + '</p>';
  });
