<?php

/**
 * GUS SOAP Client
 * A simple SOAP client that uses curl with SSL verification disabled (-k flag)
 * 
 * SECURITY WARNING:
 * This client disables SSL certificate verification (CURLOPT_SSL_VERIFYPEER = false).
 * This makes the connection vulnerable to man-in-the-middle attacks.
 * This should only be used in development/testing environments or when connecting
 * to services with self-signed certificates in a trusted network.
 * For production use, enable SSL verification and configure proper CA certificates.
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
            $errorCode = curl_errno($ch);
            curl_close($ch);
            // Log detailed error internally but provide generic message
            error_log("Curl error " . $errorCode . " while calling " . $this->endpoint);
            throw new Exception("Failed to communicate with SOAP service");
        }
        
        // Get HTTP status code
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode >= 400) {
            throw new Exception("SOAP service returned HTTP error " . $httpCode . " for endpoint: " . $this->endpoint);
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
        $xml .= '<' . htmlspecialchars($method) . '>';
        
        foreach ($params as $key => $value) {
            $xml .= '<' . htmlspecialchars($key) . '>' . htmlspecialchars($value) . '</' . htmlspecialchars($key) . '>';
        }
        
        $xml .= '</' . htmlspecialchars($method) . '>';
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
        // Disable external entity loading to prevent XXE attacks
        libxml_disable_entity_loader(true);
        
        $xml = simplexml_load_string($response, 'SimpleXMLElement', LIBXML_NOENT | LIBXML_DTDLOAD | LIBXML_DTDATTR);
        if ($xml === false) {
            throw new Exception("Failed to parse SOAP response");
        }
        return $xml;
    }
}

?>
