const researchForm = document.getElementById("research-form");
const historyForm = document.getElementById("history-form");
const historyList = document.getElementById("history-list");
const reportOutput = document.getElementById("report-output");

function clearElement(element) {
  while (element.firstChild) element.removeChild(element.firstChild);
}

function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function appendList(parent, items) {
  const ul = el("ul");
  items.forEach((item) => ul.appendChild(el("li", item)));
  parent.appendChild(ul);
}

function appendBlock(title, contentBuilder) {
  const block = el("div");
  block.className = "report-block";
  block.appendChild(el("h3", title));
  contentBuilder(block);
  reportOutput.appendChild(block);
}

function renderReport(payload) {
  clearElement(reportOutput);
  const report = payload.report;

  appendBlock("Metadata", (block) => {
    block.appendChild(
      el("p", `Research ID: ${payload.research_id} | Student ID: ${payload.student_id}`)
    );
  });

  appendBlock("Abstract", (block) => block.appendChild(el("p", report.abstract)));
  appendBlock("Introduction", (block) => block.appendChild(el("p", report.introduction)));

  appendBlock("Literature Review", (block) => {
    const ul = el("ul");
    report.literature_review.forEach((entry) => {
      ul.appendChild(el("li", `${entry.source}: ${entry.finding}`));
    });
    block.appendChild(ul);
  });

  appendBlock("Research Gaps", (block) => appendList(block, report.research_gaps));

  appendBlock("Methodology", (block) => {
    block.appendChild(el("p", report.methodology.design));
    appendList(block, report.methodology.steps);
  });

  appendBlock("Simulated Results", (block) => {
    block.appendChild(el("p", report.simulated_results.summary));
    const table = el("table");
    table.border = "1";
    table.cellPadding = "6";
    table.cellSpacing = "0";

    const thead = el("thead");
    const hr = el("tr");
    ["Metric", "Baseline", "Proposed"].forEach((h) => hr.appendChild(el("th", h)));
    thead.appendChild(hr);

    const tbody = el("tbody");
    report.simulated_results.table.forEach((row) => {
      const tr = el("tr");
      tr.appendChild(el("td", row.metric));
      tr.appendChild(el("td", row.baseline));
      tr.appendChild(el("td", row.proposed));
      tbody.appendChild(tr);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    block.appendChild(table);
  });

  appendBlock("Conclusion", (block) => block.appendChild(el("p", report.conclusion)));
  appendBlock("References", (block) => appendList(block, report.references));
  appendBlock("PPT Outline", (block) => appendList(block, report.ppt_outline));
  appendBlock("Viva Q&A", (block) => appendList(block, report.viva_questions));

  appendBlock("Datasets & Tools", (block) => {
    block.appendChild(el("p", "Datasets:"));
    appendList(block, report.datasets_and_tools.datasets);
    block.appendChild(el("p", "Tools:"));
    appendList(block, report.datasets_and_tools.tools);
  });
}

async function loadResearchDetail(researchId) {
  const response = await fetch(`/api/history/detail/${researchId}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Unable to load report detail");
  renderReport({
    research_id: data.research_id,
    student_id: data.student_id,
    report: data.report,
  });
}

researchForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    student_name: document.getElementById("student_name").value,
    student_email: document.getElementById("student_email").value,
    institution: document.getElementById("institution").value,
    topic: document.getElementById("topic").value,
    query: document.getElementById("query").value,
  };

  reportOutput.textContent = "Generating report...";

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      reportOutput.textContent = `Error: ${data.error || "Unable to generate report"}`;
      return;
    }

    renderReport(data);
  } catch (error) {
    reportOutput.textContent = `Network error: ${error.message}`;
  }
});

historyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const studentId = document.getElementById("history-student-id").value;

  historyList.textContent = "Loading...";

  try {
    const response = await fetch(`/api/history/${studentId}`);
    const data = await response.json();

    if (!response.ok) {
      historyList.innerHTML = "<li>Error loading history.</li>";
      return;
    }

    clearElement(historyList);

    if (!data.history.length) {
      historyList.innerHTML = "<li>No history available for this student.</li>";
      return;
    }

    data.history.forEach((item) => {
      const li = el("li");
      li.appendChild(el("strong", item.topic));
      li.appendChild(el("p", item.query));
      li.appendChild(el("small", item.created_at));

      const btn = el("button", "Open Report");
      btn.className = "small-button";
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Loading...";
        try {
          await loadResearchDetail(item.research_id);
        } catch (error) {
          alert(error.message);
        } finally {
          btn.disabled = false;
          btn.textContent = "Open Report";
        }
      });

      li.appendChild(btn);
      historyList.appendChild(li);
    });
  } catch (error) {
    historyList.innerHTML = `<li>Network error: ${error.message}</li>`;
  }
});
