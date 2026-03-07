type Props = {
    title: string
    data: Record<string, any>
    onClose: () => void
}

export function ComponentInfoPanel({ title, data, onClose }: Props) {

    return (
        <div
            style={{
                position: "absolute",
                right: 20,
                top: 20,
                width: 260,
                background: "rgba(0,0,0,0.85)",
                color: "white",
                padding: 16,
                borderRadius: 10,
                fontSize: 13
            }}
        >

            <div
                style={{
                    fontWeight: "bold",
                    marginBottom: 10
                }}
            >
                {title}
            </div>

            {Object.entries(data).map(([k, v]) => (
                <div key={k}>
                    {k}: {v}
                </div>
            ))}

            <button
                onClick={onClose}
                style={{
                    marginTop: 12,
                    padding: "4px 8px",
                    background: "#444",
                    color: "white",
                    borderRadius: 6
                }}
            >
                Close
            </button>

        </div>
    )
}