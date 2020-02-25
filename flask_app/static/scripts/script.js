function bttn_change_action_link() {
  return "/download/" + Math.floor(Math.random() * 100);
}

function validate_all() {
  return validate_date() && validate_summ()
}

function validate_pass() {
  var pass = document.getElementById("password");
  var pass2 = document.getElementById("password2");
  if (pass.value != pass2.value) {
    pass2.setCustomValidity("Passwords don't match.");
    pass2.reportValidity();
    return false;
  } else {
    return true;
  }
}

function validate_date() {
  var start_date = document.getElementById("start_date");
  var end_date = document.getElementById("end_date");
  if ((start_date.value) && (end_date.value)) {
    if (new Date(start_date.value).getTime() > new Date(end_date.value).getTime()) {
      start_date.setCustomValidity("Start date should be earlier than end date.");
      start_date.reportValidity();
      end_date.setCustomValidity("End date should be later than start date.");
      end_date.reportValidity();
      return false;
    } else {
      return true;
    }
  }
}

function validate_summ() {
  var start_summ = document.getElementById("start_summ");
  var end_summ = document.getElementById("end_summ");
  if ((start_summ.value) && (end_summ.value)) {
    var a = start_summ.value.replace(/[,-]/, '.');
    var b = end_summ.value.replace(/[,-]/, '.');
    if (a > b) {
      start_summ.setCustomValidity("Start summ should be less than end summ.");
      start_summ.reportValidity();
      end_summ.setCustomValidity("End summ should be more than start summ.");
      end_summ.reportValidity();
      return false;
    } else {
      return true;
    }
  }
}

function sort_table(n) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById("output_table");
  switching = true;
  // Set the sorting direction to ascending:
  dir = "asc";
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 0; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("td")[n];
      y = rows[i + 1].getElementsByTagName("td")[n];
      var x_val = parseFloat(x.innerHTML);
      var y_val = parseFloat(y.innerHTML);
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir == "asc") {
        if (!(isNaN(x_val) && isNaN(y_val))) {
          if (x_val > y_val) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
        } else if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
        }
      } else if (dir == "desc") {
        if (!(isNaN(x_val) && isNaN(y_val))) {
          if (x_val < y_val) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
        } else if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
        }
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount ++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}

function table_filter(n) {
  var input, filter, table, tr, td, i;
  input = document.getElementById("filter" + n);
  filter = input.value.toLowerCase();
  table = document.getElementById("output_table");
  tr = table.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[n];
    if (td) {
      if (td.innerHTML.toLowerCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

function find_summ() {
  var ft = document.getElementsByTagName('tfoot');
  var hd = ft[0].getElementsByTagName('th');
  for (var i = hd.length - 1; i >= 0; i--) {
    if (hd[i].innerHTML == 'summ') {
      return i;
      break;
    }
  }
}

function summ() {
  var rows = document.getElementsByTagName('tr');
  var cell, x, summ = 0;
  var n = find_summ();
  console.log(n);
  for (var i = rows.length - 2; i >= 2; i--) {
    cell = rows[i].getElementsByTagName("td")[n];
    x = parseInt(cell.innerHTML);
    summ = summ + x;
  }
  document.getElementById('summ').innerHTML = summ;
}

function reset_filter() {
  const inputs = document.getElementsByTagName('input');
  const table = document.getElementById("output_table");
  const rows = table.getElementsByTagName('tr');

  for (i = 0; i < rows.length; i++) {
    rows[i].style.display = "";
  }

  for (let i = inputs.length - 1; i >= 1; i--) {
    inputs[i].value = '';
  }
  sort_table(0);

  const index_1 = rows[0].getElementsByTagName('td')[0].innerHTML;
  const index_2 = rows[1].getElementsByTagName('td')[0].innerHTML;
  console.log(index_1, index_2);
  if (index_1 !== '1' && index_2 !== '2') {sort_table(0);}
}

function set_date() {
  var start_date = document.getElementById('start_date');
  var end_date = document.getElementById('end_date');
  var tday = new Date();
  if (!start_date.value) {
    start_date.value = tday.toISOString().slice(0, 8) + '01';
  };
  if (!end_date.value) {
    end_date.value = tday.toISOString().slice(0, 10);
  }
}
