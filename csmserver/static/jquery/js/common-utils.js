
/*
Given the field and value, returns the html code for a table row.
The argument value may contain ','.  In that case, it will be displayed
as multiple lines.
*/
function create_html_table_row(field, value) {
  var html_code = '';
  if (value != null && value.length > 0) {
    var an_array = value.split(',');
    for (var i = 0; i < an_array.length; i++) {
      if (i == 0) {
        html_code = '<tr><td>' + field + '</td><td>' + an_array[i] + '</td></tr>';
      } else {
        html_code += '<tr><td>&nbsp;</td><td>' + an_array[i] + '</td></tr>';
      }
     }
     return html_code;
   } else {
     return '';
 }       
}

function get_acceptable_string(input_string) {
  return input_string.replace(/[^a-z0-9()_-\s]/gi,'').replace(/\s+/g, " "); 
}

function get_acceptable_string_message(field, old_value, new_value) {
  return field + " '" + old_value + "' contains invalid characters.  It is recommended that it be changed to '" + new_value + "'.  Change?";
}

/*
Trims all whitespaces from lines and returns them as separate line
*/
function trim_lines(lines) {
  var result = '';
  // Use a regex to split the String literal by all whitespace (i.e. spaces/newlines/tabs). 
  var temp = lines.split(/\s+/g);
  for (var i = 0; i < temp.length; i++) {
    var line = temp[i]
    if (line.length > 0) {
      if (i == temp.length -1) {
        result += line;
      } else {
        result += line + "\n";
      }
    }  
  }
  return result;
}

function beautify_platform(platform) {
  return platform.toUpperCase().replace('_','-');
}

function get_parent_folder(directory) {
  if (directory != null) {
    var pos = directory.lastIndexOf('/');
    if (pos == -1) {
      return '';
    } else {
      return directory.substring(0, pos);
    }
  }
  return '';
}

var _MS_PER_DAY = 1000 * 60 * 60 * 24;

// a and b are javascript Date objects
function date_diff_in_days(a, b) {
  // Discard the time and time-zone information.
  var utc1 = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
  var utc2 = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());

  return Math.floor((utc2 - utc1) / _MS_PER_DAY);
}

/*
 The validate_object should be initialized as below in order to use this function.
        
 var validate_object = {
   form: current_form,
   hostname: hostname,
   server_id: $('#hidden_server').val(),
   server_directory: $('#hidden_server_directory').val(),
   software_packages: $('#software-packages').val(),
   spinner: submit_spinner,
   check_missing_file_on_server: true,
   callback: on_finish_validate
 };
*/
function on_validate_prerequisites_and_files_on_server(validate_object) {      
  check_missing_prerequisite(validate_object);     
}
      
function check_missing_prerequisite(validate_object) {               
  validate_object.spinner.show();
  
  // Only '.pie' or '.tar' files should be checked
        
  $.ajax({
     url: "/api/get_missing_prerequisite_list",
     dataType: 'json',
     data: { smu_list: trim_lines(validate_object.software_packages) , hostname: validate_object.hostname },
     success: function (data) { 
       var missing_prerequisite_list = '';
       $.each(data, function(index, element) {
         for (i = 0; i < element.length; i++) {
           missing_prerequisite_list += element[i].smu_entry + '<br>';          
         }
       });

       // There is no missing pre-requisites
       if (missing_prerequisite_list.length == 0) {
         if (validate_object.check_missing_file_on_server) {
           check_missing_files_on_server(validate_object);               
         } else {
           validate_object.callback(validate_object);
         }
       } else {
         display_missing_prerequisite_dialog(validate_object, missing_prerequisite_list);
       }        
     },
     error: function(XMLHttpRequest, textStatus, errorThrown) { 
       validate_object.spinner.hide();
     }   
   }); 
 }
      
function display_missing_prerequisite_dialog(validate_object, missing_prerequisite_list) {
     
  bootbox.dialog({
    message: missing_prerequisite_list,
    title: "Following pre-requisite(s) were not selected, but should be included.",
    buttons: {
      primary: {
        label: "Include Pre-requisites",
        className: "btn-primary",
        callback: function() {
          // Add the missing pre-requisites
          validate_object.software_packages = 
            trim_lines( validate_object.software_packages + '\n' + missing_prerequisite_list.replace(/<br>/g, "\n") )

          if (validate_object.check_missing_file_on_server) {
            check_missing_files_on_server(validate_object);
          } else {
            validate_object.callback(validate_object);
          }
        }
      }, 
      success: {
        label: "Ignore",
        className: "btn-success",
        callback: function() {
          if (validate_object.check_missing_file_on_server) {
            check_missing_files_on_server(validate_object);
          } else {
            validate_object.callback(validate_object);
          }
          validate_object.spinner.hide();
        }
      },
      main: {
        label: "Cancel",
        className: "btn-default",
        callback: function() {
          validate_object.spinner.hide();
        }
      }
    }       
  });

}
      
function check_missing_files_on_server(validate_object) {
  validate_object.spinner.show();
  
  // Only '.pie' or '.tar' files should be checked
  
  $.ajax({
     url: "/api/get_missing_files_on_server/" + validate_object.server_id,
     dataType: 'json',
     data: { smu_list: trim_lines(validate_object.software_packages), server_directory:validate_object.server_directory },
     success: function (response) { 
       if (response.status == 'Failed') {
         display_server_unreachable_dialog(validate_object);
       } else {        
         var missing_file_count = 0;
         var missing_file_list = '';
         var downloadable_file_list = '';
           
         $.each(response, function(index, element) {
           missing_file_count = element.length;
           for (i = 0; i < element.length; i++) {               
             if (element[i].is_downloadable) {
               missing_file_list += element[i].smu_entry + ' (Downloadable)<br>';
               downloadable_file_list += element[i].cco_filename + '\n';
             } else {
               missing_file_list += element[i].smu_entry + ' (Not Downloadable)<br>';
             }          
           }
         });

         // There is no missing files, go ahead and submit
         if (missing_file_count  == 0) {
           validate_object.callback(validate_object);
           // Scheduled Install will not reach the message below as the above function will cause a form submission.
           // This message is intended for the Platforms menu since there is no form submission.
           if (validate_object.form == null) {
             bootbox.alert("Requested file(s) already on the selected server repository.  No download is needed.");
           }
         } else {
           display_missing_files_dialog(validate_object, missing_file_list, downloadable_file_list);
         }
       }
     },
     error: function(XMLHttpRequest, textStatus, errorThrown) { 
       validate_object.spinner.hide();
     }
   });   
}
  
function display_missing_files_dialog(validate_object, missing_file_list, downloadable_file_list) {
  bootbox.dialog({
    message: missing_file_list,
    title: "Following files are missing on the server repository.  Those that are identified as 'Downloadable' can be downloaded from CCO.  If you choose to download them, " + 
        "the scheduled installation will not proceed until the files are successfully downloaded and copied to the server repository.",
    buttons: {
      primary: {
        label: "Download",
        className: "btn-primary",
        callback: function() { 
          validate_object.pending_downloads = downloadable_file_list
          check_cisco_authentication(validate_object)
        }
      }, 
      success: {
        label: "Ignore",
        className: "btn-success",
        callback: function() {
          validate_object.spinner.hide();
          validate_object.callback(validate_object);
        }
      },
      main: {
        label: "Cancel",
        className: "btn-default",
        callback: function() {
          validate_object.spinner.hide();
        }
      }
    }
  });
 }
  
function check_cisco_authentication(validate_object) { 
  $.ajax({
    url: "/api/check_cisco_authentication/",
    type: "POST",
    dataType: 'json',
    success: function (response) { 
      if (response.status == 'OK') {
        validate_object.callback(validate_object);
      } else {
        bootbox.alert("Cisco user authentication information has not been entered.  Go to Tools - User Preferences.");
        validate_object.spinner.hide();
      }
    },
    error: function(XMLHttpRequest, textStatus, errorThrown) { 
      validate_object.spinner.hide();
    }
  });  
}
  
function display_server_unreachable_dialog(validate_object) {
  bootbox.dialog({
    message: "CSM Server is unable to verify the existence of the software packages on the server repository.   " +
        "Either there is a network intermittent issue or the server repository is not reachable. Click Continue to schedule.",
    title: "Server repository is not reachable", 
    buttons: {
      primary: {
        label: "Continue",
        className: "btn-primary",
        callback: function() {
          validate_object.spinner.hide(); 
          validate_object.callback(validate_object);
        }
      },
      main: {
        label: "Cancel",
        className: "btn-default",
        callback: function() {
          validate_object.spinner.hide();
        }
      }
    }
  });
}