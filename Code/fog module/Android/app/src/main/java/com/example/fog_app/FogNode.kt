package com.example.fog_app

import kotlin.concurrent.thread

/* ================= CONFIG ================= */

const val SAMPLE_PERIOD = 0.5
const val WINDOW_SEC = 10.0
const val MAX_SAMPLES = (WINDOW_SEC / SAMPLE_PERIOD).toInt()
const val ESP32_IP = "192.168.213.78"

/* ================= MAIN LOOP ================= */

fun mainLoop(){

    val buffer=TelemetryBuffer(MAX_SAMPLES)
    var nextTick=System.nanoTime()
    var lastCloud=System.nanoTime()

    while(true){

        buffer.push(getDataFromESP32(ESP32_IP))

        if(buffer.full()){
            val agg=aggregate(buffer.all(), SAMPLE_PERIOD)
            val health=computeHealth(agg)

            if(health["actuation"] as Boolean){
                sendToESP32(ESP32_IP, buildActuationPacket(agg,health))
                sendToBackend(CLOUD_URL, buildCloudPacket(agg,health))
                lastCloud=System.nanoTime()
            }
            else if((System.nanoTime()-lastCloud)/1e9>=1){
                sendToBackend(CLOUD_URL, buildCloudPacket(agg,health))
                lastCloud=System.nanoTime()
            }
        }

        nextTick+=(SAMPLE_PERIOD*1e9).toLong()
        val sleep=nextTick-System.nanoTime()
        if(sleep>0) Thread.sleep(sleep/1_000_000)
    }
}

fun main(){
    println("Fog node running")
    thread(start=true,isDaemon=false){ mainLoop() }
}
