<?php

/**
 * GUS SOAP Client
 * A simple SOAP client that uses curl with SSL verification disabled (-k flag)
 */
class GUSSoapClient
{
    private $endpoint;
    private $options;

    /**
     * Constructor
     * 
     * @param string $endpoint The SOAP endpoint URL
     * @param array $options Additional options for the SOAP client
     */
    public function __construct($endpoint, $options = [])
    {
        $this->endpoint = $endpoint;
        $this->options = $options;
    }

    /**
     * Send a SOAP request using curl with SSL verification disabled
     * 
     * @param string $action The SOAP action
     * @param string $xmlRequest The XML SOAP request body
     * @return string The response from the SOAP service
     * @throws Exception If the curl request fails
     */
    public function sendRequest($action, $xmlRequest)
    {
        $ch = curl_init();
        
        // Configure curl options
        curl_setopt($ch, CURLOPT_URL, $this->endpoint);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $xmlRequest);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: text/xml; charset=utf-8',
            'SOAPAction: "' . $action . '"',
            'Content-Length: ' . strlen($xmlRequest)
        ]);
        
        // Disable SSL verification (-k flag equivalent)
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        
        // Set timeout if specified in options
        if (isset($this->options['timeout'])) {
            curl_setopt($ch, CURLOPT_TIMEOUT, $this->options['timeout']);
        }
        
        // Execute the request
        $response = curl_exec($ch);
        
        // Check for errors
        if (curl_errno($ch)) {
            $error = curl_error($ch);
            curl_close($ch);
            throw new Exception("Curl error: " . $error);
        }
        
        // Get HTTP status code
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode >= 400) {
            throw new Exception("HTTP error: " . $httpCode);
        }
        
        return $response;
    }

    /**
     * Call a SOAP method
     * 
     * @param string $method The SOAP method name
     * @param array $params The method parameters
     * @return mixed The parsed response
     */
    public function call($method, $params = [])
    {
        // Build SOAP envelope
        $xmlRequest = $this->buildSoapEnvelope($method, $params);
        
        // Send the request
        $response = $this->sendRequest($method, $xmlRequest);
        
        // Parse and return the response
        return $this->parseResponse($response);
    }

    /**
     * Build a SOAP envelope
     * 
     * @param string $method The method name
     * @param array $params The parameters
     * @return string The SOAP XML envelope
     */
    private function buildSoapEnvelope($method, $params)
    {
        $xml = '<?xml version="1.0" encoding="utf-8"?>';
        $xml .= '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">';
        $xml .= '<soap:Body>';
        $xml .= '<' . $method . '>';
        
        foreach ($params as $key => $value) {
            $xml .= '<' . $key . '>' . htmlspecialchars($value) . '</' . $key . '>';
        }
        
        $xml .= '</' . $method . '>';
        $xml .= '</soap:Body>';
        $xml .= '</soap:Envelope>';
        
        return $xml;
    }

    /**
     * Parse SOAP response
     * 
     * @param string $response The SOAP response XML
     * @return SimpleXMLElement The parsed response
     */
    private function parseResponse($response)
    {
        $xml = simplexml_load_string($response);
        if ($xml === false) {
            throw new Exception("Failed to parse SOAP response");
        }
        return $xml;
    }
}

?>
