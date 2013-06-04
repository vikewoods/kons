var aspForm = document.getElementsByName('aspnetForm')[0];
var newdiv = document.createElement('div');
var sysField = {
    'target': '__EVENTTARGET',
    'argument': '__EVENTARGUMENT',
};
newdiv.innerHTML = "<input type='hidden' name='"+sysField.target+"' id='"+sysField.target+"' value />"+
                   "<input type='hidden' name='"+sysField.argument+"' id='"+sysField.argument+"' value />";


aspForm.appendChild(newdiv);
document.getElementById(sysField.target).value   = "{{ selectName }}";
document.getElementById(sysField.argument).value = "";
aspForm.submit();