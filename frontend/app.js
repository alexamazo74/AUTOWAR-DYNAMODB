document.getElementById('postScore').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const body = {
    evaluation_id: document.getElementById('evaluationId').value,
    bp_id: document.getElementById('bpId').value,
    scores: JSON.parse(document.getElementById('scores').value || '{}')
  };
  try {
    const res = await fetch(base + '/scores', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('listScores').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('listEvalId').value;
  try {
    const res = await fetch(base + '/evaluations/' + encodeURIComponent(evalId) + '/scores');
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});
