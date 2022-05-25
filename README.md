# ms-teams-message

Function-as-a-service to send a one-to-one message between a technical account and an employee. 
You can use it as a notification channel between any application and employees.

# How to set it up 

Assuming that you already have the [OpenFaaS](https://github.com/openfaas/faas) (alternatively [faasd](https://github.com/openfaas/faasd)), the steps are:

## 1. Prepare Azure Active Directory Application

Please follow the [instruction](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app#register-an-application). Please focus on **Register an application** only.

After creating, go to **Authentication > Advanced settings > Allow public client flows** > Enable the following mobile and desktop flows:, select **Yes**.

## 2. Create secrets

You have to create a couple of **secrets**. 

Secret name | Description  
--- | --- 
`ms-teams-message-az-client-id` | `Azure Active Directory Application` Client Id  
`ms-teams-message-upn` | Your technical account `User Principal Name`
`ms-teams-message-password` |  Your technical account password
`ms-teams-message-sentry-dsn` | Sentry DSN. If you **don't want** to use it, just type anything.


```bash
faas-cli secret create ms-teams-message-az-client-id --gateway <OpenFaaS Gateway>
faas-cli secret create ms-teams-message-upn --gateway <OpenFaaS Gateway>
faas-cli secret create ms-teams-message-password --gateway <OpenFaaS Gateway>
faas-cli secret create ms-teams-message-sentry-dsn --gateway <OpenFaaS Gateway>
```

## 3. Deploy the function

```bash
faas-cli deploy -f ms-teams-message.yml --gateway <OpenFaaS Gateway>
```

# How to send a message

To send a message simply call the **POST** method on `http://<OpenFaaS Gateway>/function/ms-teams-message` with payload:

```json
{
    "recipient": "employee_user_principal_name@domain.com",
    "message": "The message body can contain HTML tags. For example you can `<b>bold some part of the message body</b>."
}
```
