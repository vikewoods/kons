var d = {{ date }};
var ds = document.getElementsByName('{{ dateSelect }}')[0];
var dl = '';
var de = false;
if (ds) {
	if (typeof d == 'number') {
		ds.children[d].selected = true;
	}
	for (i in ds.options) {
	    if (ds.options[i].value) {
	        if (i != d && ds.options[i].value != -1)
	            dl += ds.options[i].value + "\n";
	        if (typeof d == 'string' && ds.options[i].value == d) {
	            ds.options[i].selected = true;
	            de = true;
	        }
	    }
	}
	if (dl.length > 0) {
		dl.substr(0, dl.length-1);
	} else {
		if (typeof d == 'string' && de == false) {
			var newOption = document.createElement('option');
				newOption.value = d; newOption.text = d; newOption.selected = true;
				newOption.setAttribute('selected', 'selected');
			ds.appendChild(newOption);
		}
		'true';
	}
} else {
	'false';
}