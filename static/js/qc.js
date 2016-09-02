    var abbreviationBody = {
        "SP": "Servicios Parlamentarios",
        "SA": "Servicios Administrativos",
        "SME": "Servicios Medicos y Esteticos",
        "UT": "Unidad de Transferencia",
        "CS": "Communicación Social",
        "CI": "Controloría Interna",
        "AS": "Auditoría Superior",
        "IBD": "Instituto Belisario Dominguez",
        "CC": "Canal de Congreso",
        "MD": "Mesa Directiva",
        "JCP": "Junta de Coordinación Politica",
        "CO": "Comisión Ordinaria",
        "CE": "Comisión Especial",
        "CDI": "Comisión de Investigación",
        "C": "Comité",
        "GP": "Grupo Parlimentario",
        "X": "No tiene categoría preasignada"
    };

    var abbreviationAreaOfGovernment = {
        "S": "Senado",
        "D": "Camera de Diputados"
    };

    var abbreviationExpenditure = {
        "SGM": "Seguro de gastos médicos",
        "PATM": "Pasajes aereos, terrestres, maritimos",
        "G": "Gasolina",
        "P": "Peaje",
        "A": "Alimentos",
        "H": "Hospedaje",
        "PP": "Papeleria",
        "EO": "Eventos Officiales",
        "CP": "Comunicación y Publicidad",
        "SB": "Servicios Basicos (luz, agua y telefono)",
        "CRI": "Compra y Renta de Bienes Inmuebles",
        "MR": "Mantenimiento y Reperación",
        "MEO": "Mobiliario y Equipo de Oficina",
        "V": "Vehiculos",
        "SM": "Servicios Medico y de Laboritorio",
        "SPC": "Servicos Profesionales y Cientificos",
        "TS": "Transferecias al Sindicato",
        "DA": "Donativos, Ayudas Sociales y Transferencias al Extranjero",
        "VB": "Vestuario, Blancos, Articulos Deportivos",
        "BA": "Bienes Artisticos y Culturales",
        "X": "No tiene categoría preasignada"
    };

    var abbrevationLegislature = {
        "62": "Legislatura 62",
        "63": "Legislatura 63",
        "64": "Legislatura 64"
    };

    $(document).ready(function () {

        // Convert radio buttons into groups of toggle buttons.
        convertRadioButtonsToToggle();

        // Build the bxSlider
        buildSlider();

        // When we click "Other", the field for Other text should be activated
        disableButtonWhenClickingOther();

        // Customize navigating through slides so we have the "Submit button" in the last slide
        var slider = customSlideNavigationFunctions();


        // Add form enhancements
        // When hovering in the "?" after a field, show the help-text as a tooltip.
        buildToolTipText();

        buildDateButton();
        // When a user can't read the data in the PDF he can click "Can't read" link and disable that field.
        addCantReadLink();


        // Construct the category section


        addDynamicPriceFields();
        $("#purple-header").css('display', 'none');
        $(".header-white-space").css('display', 'none');
        $(document).on('click', '#submitForm', function (e) {
            $("[id^='qtip']").css('display', 'none');
            $('#document-viewer-container').parent().remove();
            $('#social_document').parent().parent().removeClass();
            $('#social_document').parent().parent().addClass('col-md-12');
            $("#purple-header").css('display', '');
            $(".header-white-space").css('display', '');
            $("#header-text").css('display', 'none');
            $("#the-logo").css('margin-top', '110px');
            $("#the-logo").css('float', 'left');
            $("#the-logo").css('position', 'absolute');
            $("#the-logo").css('margin-left', '0px');
        });
        constructCategory();


        // Design address slide.
        $('input#id_address2_domiscilio_fiscal_del_emisor').parent().parent().append("<p id='domicilio-fiscio-2'>Domicilio físico del emisor <span class='helper-block glyphicon glyphicon-question-sign' data-toggle='tooltip' data-placement='top' title='Es la dirección donde está ubicado la empresa o sucursal de ésta que expidió la factura, generalmente se ubica cerca de la razón social y el RFC' aria-hidden='true'  data-original-title='ga'></span></p><input id='same-as-above-address' type='checkbox' name='same-as-above-address' value='Bike'><p id='same-as-above-address-text'>Igual que el anterior</p>");

        buildAddressSlideFunctionality();

        // Adding the Helper Texts under the slide titles.
        $('.paso-1-de-5').append('<p>En este paso verificamos que la categoría de gasto preasignada a la factura sea correcta. Si es necesario, añadimos una categoría secundaria porque el documento contiene más de un tipo gasto.</p>');
        $('.paso-2-de-5').append('<p>Aquí registramos la cantidad total facturada; es decir, la suma que incluye el IVA. </p>');
        $('.paso-3-de-5').append('<p>Estos datos parecen aburridos, pero son importates para saber si los legisladores transfieren dinero a sus empresas.</p><p>Aquí capturamos la fecha en que se emitió la factura y los datos de quien la emitió.</p>');
        $('.paso-4-de-5').append('<p>En este paso ubicamos físicamente a la empresa y/o la sucursal que emitió la factura. Ayúdanos a capturar todos los datos que componen la dirección. </p>');
        $('.paso-5-de-5').append('<p>¿Notaste algo extraño en la factura? ¿El precio pagado por un producto o servicio es elevado? ¿El gasto te parece inúti u ofensivo (vino, motocicletas deportivas, spa, fragancias, bares y cantinas, etcétera)? ¿El emisor de la factura es un político famoso o que tú recuerdas? ¡Anótalo! Investigaremos todo lo que te resulte sospechoso.</p>');


        // Adding can't read buttons in the forth slide
        $('.paso-4-de-5-direccin').append('<a id="cant-read-second-address" class="qc-btn qc-btn-cant-read">Ilegible</a>');
        $('.paso-4-de-5-direccin').append('<a id="cant-undo-second-address" class="qc-btn qc-btn-undo" style="display: block;">Deshacer</a>');
        $('.paso-4-de-5-direccin').append('<a id="cant-read-first-address" class="qc-btn qc-btn-cant-read">Ilegible</a>');
        $('.paso-4-de-5-direccin').append('<a id="cant-undo-first-address" class="qc-btn qc-btn-undo" style="display: block;">Deshacer</a>');

        // Word count in slide 5
        $('.paso-5-de-5-hay-algo-raro').append('<div class="laWordCount">Te quedan <span id="display_count">500</span> de máximo <span id="word_left">500</span> caracteres.</div>')

        $("textarea[name='did_anything_seem_strange_on_this_factura']").attr('maxlength', '500');
        $("textarea[name='did_anything_seem_strange_on_this_factura']").on('keyup', function () {

            var length = $(this).val().length;
            if (length <= 500) {
                $('#display_count').text(500 - $(this).val().length);
            }

        });

        $('#del-recibo').prepend('<div class="candidad-helper-text">También capturamos concepto por concepto. Si te resulta más fácil, puedes resumir. Ejemplo: En lugar de escribir el título completo de un libro, puedes colocar la palabra "Libro". <br>Esta sección es opcional, pero considera que contar con información más precisa sobre los gastos de los políticos nos da a los ciudadanos mayor control sobre ellos.</div>');


        $('#chooseCategory').prepend('<div id="category-tooltip">' + $('.form-group input[name=detallesdelafactura]').parent()[0].children[1].outerHTML + '</div>');

        $('.helper-block').tooltip({delay: 0});

        $('.paso-5-de-5-hay-algo-raro').append('<a id="submit-el-forma" class="qc-btn qc-btn-submit">Enviar</a>');

        $('.paso-5-de-5-hay-algo-raro .form-group #cant_read_container').css('display', 'none');


        $('#cant-undo-first-address').css('display', "none");
        $('#cant-undo-second-address').css('display', "none");
        $('#cant-read-first-address').click(function () {
            $('input[name^=address1]').each(function () {
                $(this).attr('disabled', 'true');
                $('#cant-undo-first-address').css('display', "");
            });
        });
        $('#cant-read-second-address').click(function () {
            $('input[name^=address2]').each(function () {
                $(this).attr('disabled', 'true');
                $('#cant-undo-second-address').css('display', "");
            });
        });
        $('#cant-undo-second-address').click(function () {
            $('input[name^=address2]').each(function () {
                $(this).removeAttr('disabled');
                $('#cant-undo-second-address').css('display', "none");
            });
        });
        $('#cant-undo-first-address').click(function () {
            $('input[name^=address1]').each(function () {
                $(this).removeAttr('disabled');
                $('#cant-undo-first-address').css('display', "none");
            });
        });

        $("#elForm").submit(function (event) {
            event.preventDefault();
        });



        $(document).on('change', '#id_razon_social_del_emisor', function (e) {
            $('input[name=razon_social_del_emisor]')[0].value = $('input[name=razon_social_del_emisor]')[1].value;
        });

        $(document).on('change', '#id_nombre_comerical_de_emisor', function (e) {
            $('input[name=nombre_comerical_de_emisor]')[0].value = $('input[name=nombre_comerical_de_emisor]')[1].value;
        });
        $(document).on('change', '#id_rfc_del_emisor', function (e) {
            $('input[name=rfc_del_emisor]')[0].value = $('input[name=rfc_del_emisor]')[1].value;
        });

        // Save address1 values
        $(document).on('change', '#id_address1_calle', function (e) {
            $('input[name=address1_calle]')[0].value = $('input[name=address1_calle]')[1].value;
        });
        $(document).on('change', '#id_address1_nnext', function (e) {
            $('input[name=address1_nnext]')[0].value = $('input[name=address1_nnext]')[1].value;
        });
        $(document).on('change', '#id_address1_nint', function (e) {
            $('input[name=address1_nint]')[0].value = $('input[name=address1_nint]')[1].value;
        });
        $(document).on('change', '#id_address1_colonia', function (e) {
            $('input[name=address1_colonia]')[0].value = $('input[name=address1_colonia]')[1].value;
        });
        $(document).on('change', '#id_address1_municipio_o_delegacion', function (e) {
            $('input[name=address1_municipio_o_delegacion]')[0].value = $('input[name=address1_municipio_o_delegacion]')[1].value;
        });
        $(document).on('change', '#id_address1_codigo_postal', function (e) {
            $('input[name=address1_codigo_postal]')[0].value = $('input[name=address1_codigo_postal]')[1].value;
        });
        $(document).on('change', '#id_address1_estado', function (e) {
            $('input[name=address1_estado]')[0].value = $('input[name=address1_estado]')[1].value;
        });

        // Save address2 values
        $(document).on('change', '#id_address2_calle', function (e) {
            $('input[name=address2_calle]')[0].value = $('input[name=address2_calle]')[1].value;
        });
        $(document).on('change', '#id_address2_nnext', function (e) {
            $('input[name=address2_nnext]')[0].value = $('input[name=address2_nnext]')[1].value;
        });
        $(document).on('change', '#id_address2_nint', function (e) {
            $('input[name=address2_nint]')[0].value = $('input[name=address2_nint]')[1].value;
        });
        $(document).on('change', '#id_address2_colonia', function (e) {
            $('input[name=address2_colonia]')[0].value = $('input[name=address2_colonia]')[1].value;
        });
        $(document).on('change', '#id_address2_municipio_o_delegacion', function (e) {
            $('input[name=address2_municipio_o_delegacion]')[0].value = $('input[name=address2_municipio_o_delegacion]')[1].value;
        });
        $(document).on('change', '#id_address2_codigo_postal', function (e) {
            $('input[name=address2_codigo_postal]')[0].value = $('input[name=address2_codigo_postal]')[1].value;
        });
        $(document).on('change', '#id_address2_estado', function (e) {
            $('input[name=address2_estado]')[0].value = $('input[name=address2_estado]')[1].value;
        });

        // Save the comment in the end of the form
        $(document).on('change', '#id_did_anything_seem_strange_on_this_factura', function (e) {
            $('textarea[name=did_anything_seem_strange_on_this_factura]')[0].value = $('textarea[name=did_anything_seem_strange_on_this_factura]')[1].value;
        });



        $(document).on('change', '#same-as-above-address'), function (e) {
            $('input[name=address2_calle]')[0].value = $('input[name=address2_calle]')[1].value;
            $('input[name=address2_nnext]')[0].value = $('input[name=address2_nnext]')[1].value;
            $('input[name=address2_nint]')[0].value = $('input[name=address2_nint]')[1].value;
            $('input[name=address2_colonia]')[0].value = $('input[name=address2_colonia]')[1].value;
            $('input[name=address2_municipio_o_delegacion]')[0].value = $('input[name=address2_municipio_o_delegacion]')[1].value;
            $('input[name=address2_codigo_postal]')[0].value = $('input[name=address2_codigo_postal]')[1].value;
            $('input[name=address2_estado]')[0].value = $('input[name=address2_estado]')[1].value;
        };

        //gather all inputs of selected types
        var inputs = $('.qc-btn-select-other-optional-category, .precio, #id_rfc_del_emisor, #id_address2_estado');



        keyDownFieldsPatch();



        //bind on keydown
        inputs.on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('.bx-next').click();
                e.preventDefault();
            }
        });

    });
    function keyDownFieldsPatch(){

        $('input#id_address1_calle').on('keydown', function(e) {

            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address1_nint').focus();
                e.preventDefault();
            }
        });

        $('input#id_address1_colonia').on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address1_nnext').focus();
                e.preventDefault();
            }
        });

        $('input#id_address1_nnext').on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address1_municipio_o_delegacion').focus();
                e.preventDefault();
            }
        });

        $('input#id_address2_nnext').on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address2_municipio_o_delegacion').focus();
                e.preventDefault();
            }
        });

        $('input#id_address2_calle').on('keydown', function(e) {

            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address2_nint').focus();
                e.preventDefault();
            }
        });

        $('input#id_address2_colonia').on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address2_nnext').focus();
                e.preventDefault();
            }
        });


        $('input#id_address2_nnext').on('keydown', function(e) {
            //if we pressed the tab
            if (e.keyCode == 9 || e.which == 9) {
                $('input#id_address2_municipio_o_delegacion').focus();
                e.preventDefault();
            }
        });
    }
    function buildDateButton(){
        var date_picker_container = $('#zgjedhesi-dates').html();
        var data = $('.datefield').parent();
        $('#zgjedhesi-dates').css('display', 'none');
        $('.datefield').parent().children().css('display', 'none');
        data.append(date_picker_container);

        $('.dateti').datetimepicker({
               widgetPositioning:{
                   vertical: 'bottom'
               },
                format:"DD/MM/YYYY"

        });


        $('.fecha_de_facturaciono').each(function(idx){
            $(this).parent().parent().bind('click', function() {
                var fecha_date = $('input[name=fecha_de_facturaciono]')[1].value.split('/');
                fecha_date = fecha_date[2] + "-" + fecha_date[1] + "-" +fecha_date[0];

                $('.datefield')[1].val = fecha_date;
                $('.datefield')[1].value = fecha_date;
                $('.datefield')[0].val = fecha_date;
                $('.datefield')[0].value = fecha_date;

            });
        });
    }
    function buildAddressSlideFunctionality() {
        $('input[name="same-as-above-address"]').change(function () {
            if ($(this)['context'].checked == true) {
                $('input[name="address2_calle"]')[1].value = $('input[name="address1_calle"]')[1].value;
                $('input[name="address2_nnext"]')[1].value = $('input[name="address1_nnext"]')[1].value;
                $('input[name="address2_nint"]')[1].value = $('input[name="address1_nint"]')[1].value;
                $('input[name="address2_colonia"]')[1].value = $('input[name="address1_colonia"]')[1].value;
                $('input[name="address2_municipio_o_delegacion"]')[1].value = $('input[name="address1_municipio_o_delegacion"]')[1].value;
                $('input[name="address2_codigo_postal"]')[1].value = $('input[name="address1_codigo_postal"]')[1].value;
                $('input[name="address2_estado"]')[1].value = $('input[name="address1_estado"]')[1].value;
            }
            else {
                $('input[name="address2_calle"]')[1].value = "";
                $('input[name="address2_nnext"]')[1].value = "";
                $('input[name="address2_nint"]')[1].value = "";
                $('input[name="address2_colonia"]')[1].value = "";
                $('input[name="address2_municipio_o_delegacion"]')[1].value = "";
                $('input[name="address2_codigo_postal"]')[1].value = "";
                $('input[name="address2_estado"]')[1].value = "";
            }

        });
    }
    function constructCategory() {
        var documentViewer = $('#document-viewer-container').children()[0].data.split('/');
        var documentNameArray = documentViewer[documentViewer.length - 1].split('_');
        $('.paso-1-de-5-tipo-de-gasto div.form-group').css('display', 'none');


        var fatura_details_icon_url = "";
        if (abbreviationAreaOfGovernment[documentNameArray[0]] == "Senado") {
            fatura_details_icon_url = "/static/img/QC_Icon_01_Senato.svg";
        } else {
            fatura_details_icon_url = "/static/img/QC_Icon_01_Parliament.svg";
        }

        var category_icon_url = '';

        $('.paso-1-de-5-tipo-de-gasto').append('<br><div class="category_info"></div>');
        $('.category_info').append("<div id='factura-details-title'>Detalles de la factura</div><div id='facturaDetails'></div>");
        $('#facturaDetails').append('<table style="width:100%; border:1px solid purple;" >' +
                '<tr>' +
                '<td style="width: 90px; border:1px solid purple;"><div id="senato"><img style="float:left;" src="' + fatura_details_icon_url + '"></td>' +
                ' <td style="background:rgba(128,0,128,0.1);" rowspan="2"><div id="legislature"><p>' + abbrevationLegislature[documentNameArray[1]] + '</p></div><br><div id="abbreviationBody"><br><p > ' + abbreviationBody[documentNameArray[2]] + '</p></div></td>' +
                '</tr>' +
                '<tr >' +
                '<td><p id="abbreviationAreaOfGovernment">' + abbreviationAreaOfGovernment[documentNameArray[0]] + '</p></td>' +
                '</tr>' +
                '</table>');
        $('.category_info').append("<div id='chooseCategory'><br/><br/><p>La categoría asignada a esta factura es </p><span><img id='category-icon-image' style='float:left;' src='" + getCategoryIcon(abbreviationExpenditure[documentNameArray[3]]) + "'><h1 id='category-icon-name'>" + abbreviationExpenditure[documentNameArray[3]] + "</h1></span></div>");
        $('#chooseCategory').append("<div class='es-incorrecta'><span class='doesnt-look-right'>¿Es incorrecta?</span> <a  href='' class='qc-btn qc-btn-select-other-category' data-toggle='modal' data-target='#myModal'>Selecciona otra categoría</a></div><br/><br/><div class='optional_category'></div>");

        $('.optional_category').append("<p>Opcional </p><div id='chooseOptionalCategory'><span><img id='category-optional-icon-image' src='/static/img/icons/blank-category.svg'></span></div>");
        $('#chooseOptionalCategory').append("<div class='add-second-category'><p id='optionalCategoryText'>Asigna una categoría secundaria</p><br><br><div class=''><a href class='qc-btn qc-btn-select-other-optional-category' data-toggle='modal' data-target='#myOptionalModal'>Agregar</a></div> </div><br/><br/><br/><br/><br/><br/><br/><br/>");

        $("input[name='abbrevationlegislature']").val(abbrevationLegislature[documentNameArray[1]]);
        $("input[name='abbreviationexpenditure']").val(abbreviationExpenditure[documentNameArray[3]]);
        $("input[name='abbreviationareaofgovernment']").val(abbreviationAreaOfGovernment[documentNameArray[0]]);
        $("input[name='abbreviationbody_val']").val(abbreviationBody[documentNameArray[2]]);


        $(".qc-btn-change-cat").click(function () {
            var otraCategoriaValue = $('#otherOptionalCategoryValue').val();
            $("input[name='abbreviationexpenditure']").val(otraCategoriaValue);
            $("#category-icon-image").attr('src', "/static/img/icons/blank-category.svg");
            $('#category-icon-name').text(otraCategoriaValue);
            $('.modal').modal('hide');
        });

        $(".qc-btn-change-optional-cat").click(function () {

            var otraOptionalCategoriaValue = $('#otherSecondaryOptionalCategoryValue').val();
            $("input[name='abbreviationexpenditureoptional']").val(otraOptionalCategoriaValue);
            $('#optionalCategoryText').text(otraOptionalCategoriaValue);
            $("#category-optional-icon-image").attr('src', "/static/img/icons/blank-category.svg");
            $('.modal').modal('hide');
        });

        $(".image-category-icon").hover(
                function () {
                    var image_url = $(this).children().attr('src');
                    if (image_url != undefined) {
                        var replaced_url = image_url.replace(/(\.[\w\d_-]+)$/i, '_Hover$1');
                        $(this).children().attr('src', replaced_url);
                        $(this).addClass('selected');
                        var categoryName = image_url.split('_')[2].replace(/%20/g, ' ').replace('.svg', '');
                        $(this).click(function () {
                            $("input[name='abbreviationexpenditure']").val(categoryName);
                            $('.modal').modal('hide');
                            $("#category-icon-image").attr('src', image_url);
                            $('#category-icon-name').text(categoryName);
                        });
                    }
                }, function () {
                    var image_url = $(this).children().attr('src');
                    if (image_url != undefined) {
                        var replaced_url = image_url.replace('_Hover', '');
                        $(this).children().attr('src', replaced_url);
                        $(this).removeClass('selected');
                    }
                });

        $(".image-optional-category-icon").hover(
                function () {
                    var image_url = $(this).children().attr('src');
                    if (image_url != undefined) {
                        var replaced_url = image_url.replace(/(\.[\w\d_-]+)$/i, '_Hover$1');
                        $(this).children().attr('src', replaced_url);
                        $(this).addClass('selected');
                        var categoryName = image_url.split('_')[2].replace(/%20/g, ' ').replace('.svg', '');
                        $(this).click(function () {
                            $("input[name='abbreviationexpenditureoptional']").val(categoryName);
                            $('.modal').modal('hide');
                            $("#category-optional-icon-image").attr('src', image_url);
                            $('#optionalCategoryText').text(categoryName);
                        });
                    }
                }, function () {
                    var image_url = $(this).children().attr('src');
                    if (image_url != undefined) {
                        var replaced_url = image_url.replace('_Hover', '');
                        $(this).children().attr('src', replaced_url);
                        $(this).removeClass('selected');
                    }
                });
    }

    function getCategoryIcon(category) {
        return "/static/img/category/QC_Icon_" + category.replace(/ /g, '%20') + ".svg";

    }
    function addDynamicPriceFields() {

        $("span[id^='total_sum_number']").autoNumeric('init');
        var candidad_class = $('.paso-2-de-5-cantidad-total div.form-group').css('display', 'none');
        $('.paso-2-de-5-cantidad-total').append('<div id="precio-group"><div id="totalCon">Total&nbspcon&nbspIVA</div><div id="totalInput"><input tabindex="-1" type="text" name="totalPrecioValue"/><span id="dollar-sign">&nbsp$</span></div></div>')
        $('.paso-2-de-5-cantidad-total').append('<p class="optional">Opcional</p><div id="del-recibo"></div>');
        $('#del-recibo').append('<div style="height:30px;display:inline;">' +
                '<p style="border-color: purple;width:30%;float:left;">Descripción' +
                '</p>' +
                '<p style="width:20%;float:left;">Cantidad</p><p style="width:20%;float:left;">Precio</p><p style="width:20%;float:left;">Total</p></div>' +
                '<form class="form-inline"><div class="form-group" >' +
                ' <div class="form-group"> ' +
                '<label class="sr-only" for="description">Descripción:</label>' +
                '<input type="text" style="width: 150px;float:left; border-color: purple;" name="description" class="form-control description" id="description-0"/></div>' +
                ' <div class="form-group"> ' +
                '<label class="sr-only" for="cantidad">Cantidad:</label>' +
                '<input type="number" style="    margin-left: 10px;width: 50px;border-color: purple;" name="cantidad" class="form-control cantidad_number" id="cantidad-0"/></div>' +
                ' <div class="form-group"> ' +
                '<label class="sr-only" for="precio">Precio:</label>' +
                '<input type="text" style="    margin-left: 10px; border-color: purple;" name="precio" class="form-control precio" id="precio-0"/></div>' +
                ' <div class="form-group"> ' +
                '<div id="total_sum-0"> = $ <span id="total_sum_number-0">0</span>  </div></div>' +
                '</div>' +
                '');

        $('#del-recibo').append('<div id="grande_total_receipt_add"><a style="float:left;" class="qc-btn qc-btn-add-receipt-item" >Agregar otro concepto</a>' +
                '<br/><br/><br/>');
        var index = 1;

        $(document).on('click', '.qc-btn-add-receipt-item', function (e) {

            //do whatever
            if (index < candidad_class.length) {
                $('.qc-btn-add-receipt-item').remove();
                $('#grande_total_receipt_add').remove();
                $('#del-recibo').append('<form class="form-inline"><div class="form-group" >' +
                        ' <div class="form-group"> ' +
                        '<label class="sr-only" for="description">Description:</label>' +
                        '<input style="width: 150px;float:left; border-color: purple;" style="float:left;" type="text"  name="description" class="form-control description" id="description-' + index + '"/></div>' +
                        ' <div class="form-group"> ' +
                        '<label class="sr-only" for="cantidad">Cantidad:</label>' +
                        '<input   type="number" style="    margin-left: 10px;width: 50px;border-color: purple;"  name="cantidad"  class="form-control cantidad_number" id="cantidad-' + index + '"/></div>' +
                        ' <div class="form-group"> ' +
                        '<label class="sr-only" for="precio">Precio:</label>' +
                        '<input  type="text" style="    margin-left: 10px; border-color: purple;" name="precio" class="form-control precio" id="precio-' + index + '"/></div>' +
                        ' <div class="form-group"> ' +
                        '<div id="total_sum-' + index + '"> = $  <span id="total_sum_number-' + index + '">0</span></div></div>' +
                        '</div></form>');
                $('#del-recibo').append('<div id="grande_total_receipt_add"><a style="float:left;" class="qc-btn qc-btn-add-receipt-item">Agregar otro concepto</a>' +
                        '<br/><br/><br/>');
                $('input[name="precio"]').autoNumeric('init');
                $('*[id^="total_sum_number"]').autoNumeric('init', {});
            }
            index = index + 1;

        });

        $("input[name='totalPrecioValue']").change(function () {
            $("input[name='total_con_iva']").val($(this).val().replace(/,/g, ''));
        });
        $(document).on('change', '.cantidad_number', function (e) {
            var grande_totale = 0;
            var cantidad_id = this.id;
            var value = $(this).val();
            //do whatever
            var number_of_element = this.id.replace(/^\D+/g, '');
            var total_selector_name = '#total_sum_number-' + number_of_element;
            var value_of_all = $('#cantidad-' + number_of_element).val() * parseFloat($('#precio-' + number_of_element).val().replace(',', ''));


            var receipt_item_id = "receiptitem-" + number_of_element;
            if (number_of_element == 0) {
                $("input[name='receiptitem']").val($('#description-' + number_of_element).val() + "|" + $('#cantidad-' + number_of_element).val() + "|" + $('#precio-' + number_of_element).val());
            } else {
                $("input[name='" + receipt_item_id + "']").val($('#description-' + number_of_element).val() + "|" + $('#cantidad-' + number_of_element).val() + "|" + $('#precio-' + number_of_element).val());
            }
            $('*[id^="total_sum_number"]').each(function () {
                grande_totale = grande_totale + parseFloat(this.innerText.replace(/^\D+/g, ''));
            });
            $('*[id^="total_sum_number"]').autoNumeric('init');
            $(total_selector_name).autoNumeric('set', value_of_all);
        });

        $(document).on('change', '.precio', function (e) {
            var grande_totale = 0;
            var precio_id = this.id;
            var value = $(this).val();
            //do whatever
            var number_of_element = precio_id.replace(/^\D+/g, '');

            var total_selector_name = '#total_sum_number-' + number_of_element;
            var value_of_alla = $('#cantidad-' + number_of_element).val() * parseFloat($('#precio-' + number_of_element).val().replace(',', ''));


            var receipt_item_id = "receiptitem-" + number_of_element;
            if (number_of_element == 0) {
                $("input[name='receiptitem']").val($('#description-' + number_of_element).val() + "|" + $('#cantidad-' + number_of_element).val() + "|" + $('#precio-' + number_of_element).val());
            } else {
                $("input[name='" + receipt_item_id + "']").val($('#description-' + number_of_element).val() + "|" + $('#cantidad-' + number_of_element).val() + "|" + $('#precio-' + number_of_element).val());
            }
            $('[id^="total_sum_number"]').each(function () {
                grande_totale = grande_totale + parseFloat(this.innerText.replace(/^\D+/g, ''));
            });
            $('*[id^="total_sum_number"]').autoNumeric('init');
            $(total_selector_name).autoNumeric('set', value_of_alla);
        });


        $('input[name="totalPrecioValue"]').autoNumeric('init');
        $('input[name^="precio"]').autoNumeric('init');
        $('*input[name^="total_sum_number"]').autoNumeric('init');

    }

    function addCantReadLink() {


        $('.form-group').each(function () {
            var cant_read_container = document.createElement('div');
            cant_read_container.id = "cant_read_container";
            var cant_read = document.createElement('a');
            cant_read.setAttribute("class", "qc-btn qc-btn-cant-read");
            cant_read.innerHTML = "Ilegible";
            var undo = document.createElement('a');
            undo.innerHTML = "Deshacer";
            undo.setAttribute("class", "qc-btn qc-btn-undo");
            cant_read_container.appendChild(cant_read);
            cant_read_container.appendChild(undo);
            this.appendChild(cant_read_container);
        });


        $('.qc-btn-undo').css('display', 'none');
        $('.qc-btn-cant-read').click(function () {
            if ($(this).parent().parent().children('input').length > 0) {
                $(this).parent().parent().children('input').prop('disabled', true);
                $(this).parent().parent().find('.dateti').children('input').prop('disabled', true);
                $(this).parent().find('.qc-btn-undo').css('display', 'block');
            }
            else if ($(this).parent().parent().children('textarea').length > 0) {
                $(this).parent().parent().children('textarea').prop('disabled', true);
                $(this).parent().find('.qc-btn-undo').css('display', 'block');
            } else if ($(this).parent().parent().children('text').length > 0) {
                $(this).parent().parent().children('text').prop('disabled', true);
                $(this).parent().find('.qc-btn-undo').css('display', 'block');
            } else if ($(this).parent().parent().children().children('input').length > 0) {
                $(this).parent().parent().children().children('input').prop('disabled', true);
                $(this).parent().parent().children().children('input').css('background', "#dddddd")
                $(this).parent().find('.qc-btn-undo').css('display', 'block');
            }
        });
        $('.qc-btn-undo').click(function () {
            if ($(this).parent().parent().children('input').length > 0) {
                $(this).parent().parent().children('input').prop('disabled', false);
                $(this).parent().parent().find('.dateti').children('input').prop('disabled', false);
                $(this).parent().find('.qc-btn-undo').css('display', 'none');
            }
            else if ($(this).parent().parent().children('textarea').length > 0) {
                $(this).parent().parent().children('textarea').prop('disabled', false);
                $(this).parent().find('.qc-btn-undo').css('display', 'none');
            } else if ($(this).parent().parent().children('text').length > 0) {
                $(this).parent().parent().children('text').prop('disabled', false);
                $(this).parent().find('.qc-btn-undo').css('display', 'none');
            } else if ($(this).parent().parent().children().children('input').length > 0) {
                $(this).parent().parent().children().children('input').prop('disabled', false);
                $(this).parent().parent().children().children('input').css('background', "#fff")
                $(this).parent().find('.qc-btn-undo').css('display', 'none');
            }

        });
    }
    function customSlideNavigationFunctions() {
        var slider = $('.bxslideri').bxSlider({
            infiniteLoop: false,
            hideControlOnEnd: true,
            pager: true,
            responsive: true
        });

        $('.bx-next').click(function () {
            slider.goToNextSlide();
            navigatedToLastSlide(slider);
            return false;
        });

        $('.bx-prev').click(function () {
            slider.goToPrevSlide();
            navigatedToLastSlide(slider);
            return false;
        });

        $(".bx-pager-link").click(function () {
            var slideData = $(this).data();
            if (slideData.slideIndex == slider.getSlideCount() - 1) {
                addSubmitButtonLastSlide();
            } else {
                removeSubmitButtonLastSlide();
            }
        });

        return slider;
    }

    function disableButtonWhenClickingOther() {
        $("input[name='other_category']").prop('disabled', true);
        $("input[name='other_part_of_government_thats_responsible']").prop('disabled', true);

        $('.choicefield').change(function () {
            if ($('.choicefield#id_part_of_government_thats_responsible_7').is(':checked')) {
                $("input[name='other_part_of_government_thats_responsible']").prop('disabled', false);
            } else {
                $("input[name='other_part_of_government_thats_responsible']").prop('disabled', true);
            }

            if ($('.choicefield#id_category_13').is(':checked')) {
                $("input[name='other_category']").prop('disabled', false);
            } else {
                $("input[name='other_category']").prop('disabled', true);
            }

        });
    }

    function convertRadioButtonsToToggle() {
        $("#elForm input:radio").parent().parent().parent().addClass("btn-group");
        $("#elForm input:radio").parent().parent().addClass("btn checkbox-btn ");
        $("#elForm input:radio").parent().parent().parent().attr("data-toggle", "buttons");
        $("#elForm input:radio").parent().parent().css('width', '45%').css('border', '1px solid white');

        $('input:radio').toggle();

        $('[id*="radio-popup-style-"]').click(function () {
            $(this).prop('checked', true).parent().addClass('active');
            $('[id*="radio-popup-style-"]').not($(this)).removeAttr('checked').prop('checked', false).parent().removeClass('active');
        });
    }

    function navigatedToLastSlide(slider) {
        var numberOfSlides = slider.getSlideCount() - 1;

        var navigatedToLastSlide = false;

        if (slider.getCurrentSlide() == numberOfSlides) {
            navigatedToLastSlide = true;
        }

        if (navigatedToLastSlide == true) {
            addSubmitButtonLastSlide();
        }
        else {
            removeSubmitButtonLastSlide();
        }
        return navigatedToLastSlide;
    }

    function addSubmitButtonLastSlide() {
        $('.bx-wrapper .bx-controls-direction a').children().eq(1).remove();

        // First we check if there is a submit button added
        // Doing this so we don't end up adding buttons everytime we click the slide controlls.
        if ($('.bx-wrapper .bx-controls-direction').has('button').length == 0) {

        } else {
            $('.bx-wrapper .bx-controls-direction button').remove();
        }
    }

    function removeSubmitButtonLastSlide() {
        // This function should be called only when you need to remove the submit button which comes
        // instead of the arrow in the slides.
        $('.bx-wrapper .bx-controls-direction button').remove();
    }

    function buildSlider() {
        // Get all the elements that have class="sections"
        var groupOfElements = document.getElementsByClassName('sections');

        // Declare the empty array to later fill with the sections names
        var allSections = [];

        // Save the names of the sections
        for (i = 0; i < groupOfElements.length; i++) {
            allSections[i] = slugify(jQuery.trim(groupOfElements[i].attributes.id.nodeValue));
        }

        // Get distinct section values
        var uniqueSections = allSections.filter(function (itm, i, allSections) {
            return i == allSections.indexOf(itm);
        });

        // Group and render the fields in slide mode
        for (var i = 0; i < groupOfElements.length; i++) {
            for (var j = 0; j < uniqueSections.length; j++) {
                if (slugify(jQuery.trim(groupOfElements[i].attributes.id.nodeValue)) == uniqueSections[j]) {
                    if ($("." + uniqueSections[j]).length > 0) {
                        // Adding other elements of the group(section)
                        $('.' + uniqueSections[j]).append('<div class="form-group">' + groupOfElements[i].innerHTML + '</div>');
                    }
                    else {
                        // If we are showing the first element of the form group(section) we are showing the tittle too.
                        var slide_title = groupOfElements[i].id.split(":");
                        $(".bxslideri").append('<li class="' + uniqueSections[j] + '">' + '<div class="title-of-slide"><span class="slide-first-title">' + slide_title[0] + ':</span>' + '<span class="slide-title">' + slide_title[1] + '</span></div>' + '<div class="' + slugify(slide_title[0]) + '">' + '</div>' + '<div class="form-group">' + getFormElement(groupOfElements[i]) + '</div></li>');

                    }
                }
            }
        }
    }

    function getFormElement(element) {

        return element.innerHTML;
    }

    // Slugify the strings
    function slugify(text) {
        return text.toString().toLowerCase()
                .replace(/\s+/g, '-')           // Replace spaces with -
                .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
                .replace(/\-\-+/g, '-')         // Replace multiple - with single -
                .replace(/^-+/, '')             // Trim - from start of text
                .replace(/-+$/, '');            // Trim - from end of text
    }

    function buildToolTipText() {

        $('.help-block').each(function () {
            if (this.innerHTML != "") {
                $(this).attr('data-toggle', 'tooltip');
                $(this).attr('data-placement', 'top');
                $(this).attr('title', "" + this.innerHTML + "");
                $(this).attr('class', 'helper-block glyphicon glyphicon-question-sign');
                $(this).attr('aria-hidden', 'true');
                this.innerText = "";
                this.innerHTML = "";
                $(this).innerText = "";
            } else {
                $(this).attr("style", "display:none;");
            }

        });


    }

