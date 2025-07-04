const queryParams = new URLSearchParams(window.location.search);
const query = queryParams.get('query');
const title = document.getElementById('panel-title');
const form = document.getElementById('query-form');
const studentField = document.getElementById('student-field');
const dateField = document.getElementById('date-field');
const resultPanel = document.getElementById('result-output');

const titles = {
  total: "📋 View Total Attendance Records",
  date: "🗓️ View Attendance by Date",
  student_date: "🔍 Check Student on Specific Date",
  percentage: "📊 View Student Attendance Percentage"
};

if (query && titles[query]) {
  title.innerText = titles[query];
  form.classList.remove('hidden');

  if (query === 'total') {
    form.classList.add('hidden');
    resultPanel.classList.remove('hidden');
    resultPanel.innerHTML = `<p>Showing all attendance records...</p>`;
  } else if (query === 'date') {
    dateField.classList.remove('hidden');
  } else if (query === 'student_date') {
    studentField.classList.remove('hidden');
    dateField.classList.remove('hidden');
  } else if (query === 'percentage') {
    studentField.classList.remove('hidden');
  }
} else {
  title.innerText = "❌ Invalid Query Type";
}

form?.addEventListener('submit', function (e) {
  e.preventDefault();
  resultPanel.classList.remove('hidden');

  const student = document.getElementById('student')?.value;
  const date = document.getElementById('date')?.value;

  if (query === 'date') {
    resultPanel.innerHTML = `<p>Showing attendance records for <strong>${date}</strong>.</p>`;
  } else if (query === 'student_date') {
    resultPanel.innerHTML = `<p><strong>${student}</strong> was present on <strong>${date}</strong>.</p>`;
  } else if (query === 'percentage') {
    resultPanel.innerHTML = `<p><strong>${student}</strong> has 92.5% attendance.</p>`;
  }
});
