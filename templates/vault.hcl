storage "file" {
	path = "/home/yshalenyk/work/op/billing/var/vault/vault"
}

listener "tcp" {
	address = "{{ address }}"
	tls_disable = {{ disable_tls }}
}

disable_mlock = true
