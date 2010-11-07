document.onkeyup = Navigate; // if key is pressed call function for navigation

function Navigate(key)
{
	var _Key = (window.event) ? event.keyCode : key.keyCode;
	switch(_Key) 
	{
		case 37: //arrow left
			window.location = nav(-1); break;
		case 39: //arrow right
			window.location = nav(+1); break;
	}
}

function nav(direction)
{
   if (direction == -1)
       return document.getElementById("previousphoto");
   else
       return document.getElementById("nextphoto");
}
