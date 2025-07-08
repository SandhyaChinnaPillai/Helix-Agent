"use client";
import RootLayout from "./layout";
import { SocketProvider } from "../context/SocketProvider";
import HelixComponent from "../components/HelixComponent";

export default function HomePage() {

    return (
        <SocketProvider >
            <RootLayout
                children={<HelixComponent />}
            />
        </SocketProvider>
    )

}