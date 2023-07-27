// Autocompletado de direcciones para el campo de entrada de origen
const OriginForn = document.getElementById('Origin_form');
const OriginAutocomplete = new google.maps.places.Autocomplete(OriginForn);

// Autocompletado de direcciones para los campos de entrada de destino
const DestinoInputs = document.querySelectorAll('.Destino_input'); //Usamos la Class para obtener todos los parametros
//de entrada de Destino
DestinoInputs.forEach((input) =>{ //Esto es un bucle FOR que recorre la lista de entradas DESTINO para crear su automompletado
    const DestinoAutocomplete = new google.maps.places.Autocomplete(input);
});

// Agregar nuevos campos de entrada de destino cuando se hace clic en el botón "Agregar Destino"
const AddDestinoBtn = document.getElementById('Add-Detino-btn'); //Obtenemos el boton de Agregar destino
AddDestinoBtn.addEventListener('click',()=>{ //Agregamos una funcionalidad al dar Click
    const ContainerDestinos = document.getElementById('destinos'); //Obtenemos el DIV donde estan almacenados todos los DIV de inputs Destinos
    const NewDestino = document.createElement('div');//Creamos un nuevo DIV de input Destino
    NewDestino.classList.add("mb-3");//Agregamos la Class al Div que creamos
    NewDestino.innerHTML = `
    <input type="text" class="form-control Destino_input" id="Destino_form" placeholder="Dirección de Destino">
    `; //Aqui agregamos el contenido dentro del DIV (Nuestro imput)
    ContainerDestinos.appendChild(NewDestino);//Agregamos el nuevo DIV creado al DIV contenedor de los inputs Destino
    
    const NewDestinoAutocomplete = new google.maps.places.Autocomplete(NewDestino.querySelector('.Destino_input'));

});

// Lógica para enviar los datos al backend cuando se hace clic en el botón "Generate Route"
const Route_Maker = document.getElementById('RM');//Obtenemos el bton para crear rutas
Route_Maker.addEventListener('click', () => { //Agregamos duncionalidad al dar Click
    const Origin = document.getElementById('Origin_form');//Obtenemos el Origen
    const All_Destinos = document.querySelectorAll('.Destino_input');//Obtenemos lso Destinos

    const Origin_Adress = Origin.value;//Obtenemos los Valores ingresados en el elemento HTML input
    const Destino_Adress = Array.from(All_Destinos).map(input => input.value);//Convertimos en un Array la lsita de inputs Destinos
    //Luego con Map (como una lambda de python) Obtenemos el valor ingresado en los imput HTML de Destinos

    const Addresses = [Origin_Adress, ...Destino_Adress];//Convertimos en una lista todas las Direcciones Obtenidas

    fetch('/Create_Routes/',{//Aqui enviamos la solicitud HTTPS al Backend
        method  : 'POST',
        headers : {
            'Content-Type' : 'application/json',
        },
        body    : JSON.stringify({ Addresses}),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });

})