package com.example.mantenimientoapp.data.remote.dto

data class NetworkIpDto(
    val ip: String,
    val label: String,
    val iface: String
)

data class NetworkInfoDto(
    val port: Int,
    val ips: List<NetworkIpDto>,
    val urls: List<String>
)
