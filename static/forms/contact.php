<?php
	if (isset($_POST["submit"])) {
		$name = $_POST['name'];
		$email = $_POST['email'];
		$message = $_POST['message'];
		
		$from = $email; 
		
		// WARNING: Be sure to change this. This is the address that the email will be sent to
		$to = 'gta.thelegend@gmail.com'; 
		
		$subject = "Message from ".$name." ";
		
		$body = "From: $name\n E-Mail: $email\n Message:\n $message";
 
		
		
    mail ($to, $subject, $body, $from);
// If there are no errors, send the email
// if (!$errName && !$errEmail && !$errMessage && !$errHuman) {
// 	if () {
// 		$result='<div class="alert alert-success">Thank You! I will be in touch</div>';
// 	} else {
// 		$result='<div class="alert alert-danger">Sorry there was an error sending your message. Please try again later</div>';
// 	}
// }
	}
?>