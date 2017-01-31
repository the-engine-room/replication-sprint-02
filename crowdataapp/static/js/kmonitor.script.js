/** functions **/

/** add lines for multiple values in data entry **/
function sectionRepeat(){
  var repeatBlock = [];
  $('button.repeater').each(function( i ){
    repeatBlock.push( $(this).prev().clone() );
  });

  $('button.repeater').click(function(e){
    e.preventDefault();

    var repeaterClone = $(this).prev().clone();
    /** reset inputs and selects **/
    repeaterClone.find('input').val('');
    repeaterClone.find('select').val('choose');
    repeaterClone.find('select + input[type="text"]').addClass('hidden').removeClass('show');

    $(repeaterClone).insertAfter($(this).prev());

    /** bind recursively to newly generated elements **/
    $(repeaterClone).on('click', 'button.repeater', function(){ sectionRepeat(); });
    $(repeaterClone).on('change', 'select', function(){ otherInput(); });
  });
}

/** display input field to enter "other" value **/
function otherInput(){
  $('select').change(function(){
    if($(this).val() == 'other'){
      $(this).next('input[type="text"]').addClass('show').removeClass('hidden').focus();
    }
    else {
      $(this).next('input[type="text"]').addClass('hidden').removeClass('show');
    }
  });
}
/** main js script **/
$(document).ready(function(){

  console.log('started...');

  /** section repeat/add lines **/
  sectionRepeat();
  /** the "other" input field for selects **/
  otherInput();

  /** box toggling **/
  $('.box-toggler:radio').change(function(){
    if($(this).val() == 'yes'){
      $($(this).data('toggle-target')).removeClass('hidden').addClass('show');
      $($(this).data('toggle-target') + ' + button.hidden').removeClass('hidden').addClass('show');
    }
    else {
      $($(this).data('toggle-target')).addClass('hidden').removeClass('show');
      $($(this).data('toggle-target') + ' + button.repeater').addClass('hidden').removeClass('show');
    }
  });

});
