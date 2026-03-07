package com.example.fog_app

import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.unit.dp

@Composable
fun HomeScreen(
    userType: UserType,
    onTileClick: (String) -> Unit,
    onLogsClick: () -> Unit,
    dashboardUrl: String,
    onUrlChange: (String) -> Unit
) {
    when (userType) {
        UserType.USER -> UserHomeScreen(dashboardUrl)
        UserType.DEVELOPER -> DeveloperHomeScreen(onLogsClick, dashboardUrl, onUrlChange)
    }
}

@Composable
fun UserHomeScreen(url: String) {
    Surface(color = Color.Black, modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.fillMaxSize().padding(top = 32.dp)) {
            var webView: WebView? = null
            
            AndroidView(
                factory = { context ->
                    WebView(context).apply {
                        webViewClient = object : WebViewClient() {
                            override fun onPageFinished(view: WebView?, url: String?) {
                                super.onPageFinished(view, url)
                                if (url?.contains("login") == true) {
                                    val js = """
                                        (function() {
                                            var inputs = document.getElementsByTagName('input');
                                            for (var i = 0; i < inputs.length; i++) {
                                                if (inputs[i].type === 'email' || inputs[i].name === 'email' || inputs[i].id === 'email') {
                                                    inputs[i].value = 'starlender.16@gmail.com';
                                                }
                                                if (inputs[i].type === 'password' || inputs[i].name === 'password' || inputs[i].id === 'password') {
                                                    inputs[i].value = 'JustD00it!';
                                                }
                                            }
                                            // Optional: Try to find and click the login button
                                            var buttons = document.getElementsByTagName('button');
                                            for (var j = 0; j < buttons.length; j++) {
                                                if (buttons[j].innerText.toLowerCase().includes('login') || buttons[j].type === 'submit') {
                                                    // buttons[j].click(); // Uncomment to auto-submit
                                                }
                                            }
                                        })();
                                    """.trimIndent()
                                    view?.evaluateJavascript(js, null)
                                }
                            }
                        }
                        settings.apply {
                            javaScriptEnabled = true
                            domStorageEnabled = true
                            loadWithOverviewMode = true
                            useWideViewPort = true
                            setSupportZoom(true)
                            builtInZoomControls = true
                            displayZoomControls = false
                        }
                        loadUrl(url)
                        webView = this
                    }
                },
                modifier = Modifier.fillMaxSize(),
                update = { it.loadUrl(url) }
            )

            BackHandler(enabled = true) {
                if (webView?.canGoBack() == true) {
                    webView?.goBack()
                }
            }
        }
    }
}

@Composable
fun DeveloperHomeScreen(onLogsClick: () -> Unit, dashboardUrl: String, onUrlChange: (String) -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        OutlinedTextField(
            value = dashboardUrl,
            onValueChange = onUrlChange,
            label = { Text("Dashboard URL") },
            modifier = Modifier.fillMaxWidth(),
            colors = TextFieldDefaults.colors(
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedContainerColor = Color.DarkGray,
                unfocusedContainerColor = Color.DarkGray
            )
        )
        Spacer(modifier = Modifier.height(32.dp))
        Button(onClick = onLogsClick) {
            Text("View Logs")
        }
    }
}
